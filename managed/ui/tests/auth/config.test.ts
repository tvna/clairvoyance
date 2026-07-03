import { afterEach, describe, expect, it, vi } from "vitest";
import { loadRuntimeConfig, RuntimeConfigError } from "../../src/auth/config";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("loadRuntimeConfig", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("parses a complete config.json", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(200, {
          issuer: "https://idp.example.com",
          client_id: "clairvoyance-ui",
          audience: "clairvoyance-managed",
          org_claim: "org",
          roles_claim: "roles",
        }),
      ),
    );
    const config = await loadRuntimeConfig();
    expect(config.issuer).toBe("https://idp.example.com");
    expect(config.authorization_endpoint).toBeUndefined();
  });

  it("throws RuntimeConfigError when a required field is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { issuer: "https://idp.example.com" })),
    );
    await expect(loadRuntimeConfig()).rejects.toBeInstanceOf(RuntimeConfigError);
  });

  it("throws RuntimeConfigError on a non-OK response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(500, {})));
    await expect(loadRuntimeConfig()).rejects.toBeInstanceOf(RuntimeConfigError);
  });

  it("throws RuntimeConfigError when fetch itself fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(loadRuntimeConfig()).rejects.toBeInstanceOf(RuntimeConfigError);
  });
});
