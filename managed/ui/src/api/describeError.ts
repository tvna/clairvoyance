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
} from "./errors";

export interface ErrorDescription {
  kind:
    | "forbidden"
    | "not-found"
    | "auth-expired"
    | "config-unavailable"
    | "transient"
    | "validation"
    | "unexpected";
  message: string;
}

/** Maps a thrown apiFetch error to display copy (design §8's table). */
export function describeApiError(error: unknown): ErrorDescription {
  if (error instanceof ForbiddenError) {
    return { kind: "forbidden", message: error.detail };
  }
  if (error instanceof NotFoundError) {
    return { kind: "not-found", message: error.detail };
  }
  if (error instanceof AuthExpiredError) {
    return { kind: "auth-expired", message: "Your session expired. Redirecting to sign in…" };
  }
  if (error instanceof ConfigUnavailableError) {
    return {
      kind: "config-unavailable",
      message: "Admin sign-in is not configured on the server. Contact your operator.",
    };
  }
  if (error instanceof TransientUnavailableError) {
    return {
      kind: "transient",
      message: "The identity provider is temporarily unavailable. Retrying…",
    };
  }
  if (error instanceof ValidationError) {
    return { kind: "validation", message: error.message };
  }
  if (error instanceof NetworkError) {
    return {
      kind: "unexpected",
      message: "Network request failed. Check your connection and retry.",
    };
  }
  if (error instanceof ContractError) {
    return {
      kind: "unexpected",
      message: "The server response didn't match what this UI expects. Please report this.",
    };
  }
  if (error instanceof UnexpectedApiError) {
    return { kind: "unexpected", message: `Unexpected server error (${error.status}).` };
  }
  return { kind: "unexpected", message: "Something went wrong." };
}
