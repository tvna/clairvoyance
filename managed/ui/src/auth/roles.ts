/** Mirrors app/auth/rbac.py's Role enum and parse_roles. */

export const ROLES = ["org_admin", "team_manager", "coach", "auditor"] as const;

export type Role = (typeof ROLES)[number];

// Design §2's capability table.
export const READ_ROLES: readonly Role[] = ["org_admin", "team_manager", "coach", "auditor"];
export const POLICY_WRITE_ROLES: readonly Role[] = ["org_admin"];
export const AUDIT_READ_ROLES: readonly Role[] = ["org_admin", "auditor"];

/** Maps the roles claim to known roles, ignoring foreign entries (parse_roles mirror). */
export function parseRoles(raw: unknown): ReadonlySet<Role> {
  if (!Array.isArray(raw)) {
    return new Set();
  }
  const known = new Set<string>(ROLES);
  return new Set(raw.filter((item): item is Role => typeof item === "string" && known.has(item)));
}

export function hasAnyRole(roles: ReadonlySet<Role>, allowed: readonly Role[]): boolean {
  return allowed.some((role) => roles.has(role));
}
