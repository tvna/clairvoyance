/**
 * Shared fetch layer (design §8). One function maps every admin API
 * response to a typed result or a typed error; screens render states,
 * they do not interpret status codes.
 *
 * Auth is wired via configureApiAuth() rather than importing the auth
 * module directly, so this module has no dependency on oidc-client-ts.
 */

import type { z } from "zod";
import {
  AuthExpiredError,
  ConfigUnavailableError,
  ContractError,
  ForbiddenError,
  isRecord,
  NetworkError,
  NotFoundError,
  TransientUnavailableError,
  UnexpectedApiError,
  ValidationError,
} from "./errors";

// Mirrors of the literal `detail` strings raised in managed/app/deps.py
// (get_admin_principal). The pairing is enforced by a drift gate:
// managed/tests/test_admin_api.py asserts the backend emits exactly these
// strings, so a backend rewording fails backend CI instead of silently
// degrading both 503s to UnexpectedApiError here.
const OIDC_NOT_CONFIGURED_DETAIL = "admin OIDC is not configured";
const JWKS_UNAVAILABLE_DETAIL = "OIDC JWKS endpoint is unavailable";

type AccessTokenProvider = () => string | null;
/** Attempt one non-iframe silent renew; resolves true if the caller should retry. */
type UnauthorizedHandler = () => Promise<boolean>;
/** Drop the local session so RequireAuth actually redirects to sign-in. */
type AuthExpiredHandler = () => Promise<void>;

let getAccessToken: AccessTokenProvider = () => null;
let onUnauthorized: UnauthorizedHandler = async () => false;
let onAuthExpired: AuthExpiredHandler = async () => {};

export function configureApiAuth(opts: {
  getAccessToken: AccessTokenProvider;
  onUnauthorized: UnauthorizedHandler;
  onAuthExpired: AuthExpiredHandler;
}): void {
  getAccessToken = opts.getAccessToken;
  onUnauthorized = opts.onUnauthorized;
  onAuthExpired = opts.onAuthExpired;
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

export interface ApiFetchOptions {
  method?: "GET" | "PUT";
  body?: unknown;
}

export async function apiFetch<T>(
  path: string,
  schema: z.ZodType<T>,
  options: ApiFetchOptions = {},
  attempt = 0,
): Promise<T> {
  const token = getAccessToken();
  let response: Response;
  try {
    response = await fetch(path, {
      method: options.method ?? "GET",
      headers: {
        ...(token !== null ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
    });
  } catch (cause) {
    throw new NetworkError("network request failed", { cause });
  }

  if (response.status === 401) {
    if (attempt === 0 && (await onUnauthorized())) {
      return apiFetch(path, schema, options, attempt + 1);
    }
    // Every path that gives up on the session must also end it, or the
    // "Redirecting to sign in…" copy for AuthExpiredError is a lie: this
    // covers both a renew that fails without throwing and a renewed token
    // the server still rejects.
    await onAuthExpired();
    throw new AuthExpiredError("admin session expired");
  }

  if (!response.ok) {
    const body = await safeJson(response);
    const detail = isRecord(body) ? body.detail : undefined;
    if (response.status === 403) {
      throw new ForbiddenError(typeof detail === "string" ? detail : "insufficient role");
    }
    if (response.status === 404) {
      throw new NotFoundError(typeof detail === "string" ? detail : "not found");
    }
    if (response.status === 422) {
      throw new ValidationError(detail);
    }
    if (response.status === 503) {
      if (detail === OIDC_NOT_CONFIGURED_DETAIL) {
        throw new ConfigUnavailableError(detail);
      }
      if (detail === JWKS_UNAVAILABLE_DETAIL) {
        throw new TransientUnavailableError(detail);
      }
    }
    throw new UnexpectedApiError(response.status, detail);
  }

  const json = await safeJson(response);
  const parsed = schema.safeParse(json);
  if (!parsed.success) {
    throw new ContractError(`response for ${path} did not match the expected schema`, parsed.error);
  }
  return parsed.data;
}

/**
 * TanStack Query `retry` option (design §4/§8): only network errors and the
 * transient-JWKS 503 are retried, capped at 3 — every other error (resolved
 * 4xx, the config-503, contract mismatches) is never retried, since every
 * admin request is audited server-side and blind retries multiply audit
 * rows.
 */
export function shouldRetryApiError(failureCount: number, error: unknown): boolean {
  if (failureCount >= 3) {
    return false;
  }
  return error instanceof NetworkError || error instanceof TransientUnavailableError;
}
