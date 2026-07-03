/**
 * Typed errors for the shared fetch layer's error contract (design §8).
 * Screens render states from these types; they do not interpret status
 * codes themselves.
 */

export class NetworkError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "NetworkError";
  }
}

export class AuthExpiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthExpiredError";
  }
}

export class ForbiddenError extends Error {
  constructor(public readonly detail: string) {
    super(detail);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends Error {
  constructor(public readonly detail: string) {
    super(detail);
    this.name = "NotFoundError";
  }
}

export class ValidationError extends Error {
  constructor(public readonly detail: unknown) {
    super(formatValidationDetail(detail));
    this.name = "ValidationError";
  }
}

/** 503 "admin OIDC is not configured" — operator problem, not transient. */
export class ConfigUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigUnavailableError";
  }
}

/** 503 "OIDC JWKS endpoint is unavailable" — transient infra, bounded retry. */
export class TransientUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TransientUnavailableError";
  }
}

/** Response shape didn't match the zod contract schema — fails loud. */
export class ContractError extends Error {
  constructor(
    message: string,
    public readonly cause: unknown,
  ) {
    super(message);
    this.name = "ContractError";
  }
}

/** Any status/shape not covered by the design §8 table. Never swallowed. */
export class UnexpectedApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: unknown,
  ) {
    super(`unexpected ${status} response`);
    this.name = "UnexpectedApiError";
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function formatValidationDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        isRecord(item) && typeof item.msg === "string" ? item.msg : JSON.stringify(item),
      )
      .join("; ");
  }
  return JSON.stringify(detail);
}
