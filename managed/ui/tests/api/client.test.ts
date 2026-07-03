import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { apiFetch, configureApiAuth, shouldRetryApiError } from "../../src/api/client";
import {
  AuthExpiredError,
  ConfigUnavailableError,
  ContractError,
  ForbiddenError,
  NetworkError,
  NotFoundError,
  TransientUnavailableError,
  UnexpectedApiError,
  ValidationError,
} from "../../src/api/errors";

const EchoSchema = z.object({ ok: z.boolean() });

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("apiFetch", () => {
  beforeEach(() => {
    configureApiAuth({ getAccessToken: () => "test-token", onUnauthorized: async () => false });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed data on 200", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { ok: true })));
    await expect(apiFetch("/v1/admin/x", EchoSchema)).resolves.toEqual({ ok: true });
  });

  it("throws NetworkError when fetch rejects", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(NetworkError);
  });

  it("throws ContractError when the response does not match the schema", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { ok: "not-a-boolean" })));
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(ContractError);
  });

  it("throws ForbiddenError on 403", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(403, { detail: "insufficient role" })),
    );
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toMatchObject(
      new ForbiddenError("insufficient role"),
    );
  });

  it("throws NotFoundError on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(404, { detail: "contributor not found" })),
    );
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(NotFoundError);
  });

  it("throws ValidationError on 422 carrying the detail verbatim", async () => {
    const detail = [
      { loc: ["body", "settings", "retention_days"], msg: "retention_days cannot be null" },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(422, { detail })));
    const rejection = apiFetch("/v1/admin/x", EchoSchema);
    await expect(rejection).rejects.toBeInstanceOf(ValidationError);
    await rejection.catch((error: ValidationError) => {
      expect(error.detail).toEqual(detail);
      expect(error.message).toContain("retention_days cannot be null");
    });
  });

  it("distinguishes the two 503 states by detail string (design §8)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(503, { detail: "admin OIDC is not configured" })),
    );
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(
      ConfigUnavailableError,
    );

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(503, { detail: "OIDC JWKS endpoint is unavailable" })),
    );
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(
      TransientUnavailableError,
    );
  });

  it("throws UnexpectedApiError on an unrecognized 503 detail (never fails open)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(503, { detail: "something else" })),
    );
    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(UnexpectedApiError);
  });

  it("retries once via onUnauthorized on 401, then succeeds", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "invalid admin token" }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    configureApiAuth({ getAccessToken: () => "test-token", onUnauthorized: async () => true });

    await expect(apiFetch("/v1/admin/x", EchoSchema)).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("throws AuthExpiredError on 401 without a retry loop when renewal fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "invalid admin token" }));
    vi.stubGlobal("fetch", fetchMock);
    configureApiAuth({ getAccessToken: () => "test-token", onUnauthorized: async () => false });

    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(AuthExpiredError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not retry a second 401 even if onUnauthorized keeps returning true", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "invalid admin token" }));
    vi.stubGlobal("fetch", fetchMock);
    configureApiAuth({ getAccessToken: () => "test-token", onUnauthorized: async () => true });

    await expect(apiFetch("/v1/admin/x", EchoSchema)).rejects.toBeInstanceOf(AuthExpiredError);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});

describe("shouldRetryApiError", () => {
  it("retries NetworkError and TransientUnavailableError up to 3 times", () => {
    expect(shouldRetryApiError(0, new NetworkError("x"))).toBe(true);
    expect(shouldRetryApiError(2, new TransientUnavailableError("x"))).toBe(true);
    expect(shouldRetryApiError(3, new NetworkError("x"))).toBe(false);
  });

  it("never retries resolved 4xx/5xx errors or contract mismatches", () => {
    expect(shouldRetryApiError(0, new ForbiddenError("x"))).toBe(false);
    expect(shouldRetryApiError(0, new NotFoundError("x"))).toBe(false);
    expect(shouldRetryApiError(0, new ConfigUnavailableError("x"))).toBe(false);
    expect(shouldRetryApiError(0, new ContractError("x", undefined))).toBe(false);
  });
});
