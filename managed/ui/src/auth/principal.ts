import { isRecord } from "../api/errors";
import { decodeJwtPayload } from "./jwt";
import { parseRoles, type Role } from "./roles";

export interface AdminPrincipal {
  subject: string;
  organizationKey: string;
  roles: ReadonlySet<Role>;
}

/**
 * Derives the principal from the *access* token, not oidc-client-ts's
 * `User.profile` (which decodes the id_token). app/deps.py verifies the
 * bearer/access token and reads org/roles from it — the SPA must read the
 * same claims from the same token, or nav gets shaped from the wrong
 * source in a provider that puts different claims on each token.
 */
export function principalFromAccessToken(
  accessToken: string,
  orgClaim: string,
  rolesClaim: string,
): AdminPrincipal {
  const payload = decodeJwtPayload(accessToken);
  if (!isRecord(payload)) {
    throw new Error("access token payload is not a JSON object");
  }
  const subject = payload.sub;
  const organizationKey = payload[orgClaim];
  if (typeof subject !== "string" || subject === "") {
    throw new Error("access token is missing a subject claim");
  }
  if (typeof organizationKey !== "string" || organizationKey === "") {
    throw new Error(`access token is missing the organization claim '${orgClaim}'`);
  }
  return {
    subject,
    organizationKey,
    roles: parseRoles(payload[rolesClaim]),
  };
}
