import { describe, expect, it } from "vitest";
import { principalFromAccessToken } from "../../src/auth/principal";

function fakeToken(claims: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const payload = btoa(JSON.stringify(claims));
  return `${header}.${payload}.signature`;
}

describe("principalFromAccessToken", () => {
  it("reads sub/org/roles from the access token, ignoring unknown roles", () => {
    const token = fakeToken({
      sub: "admin@example.com",
      org: "acme",
      roles: ["org_admin", "coach", "not-a-known-role"],
    });
    const principal = principalFromAccessToken(token, "org", "roles");
    expect(principal.subject).toBe("admin@example.com");
    expect(principal.organizationKey).toBe("acme");
    expect(principal.roles).toEqual(new Set(["org_admin", "coach"]));
  });

  it("honors custom claim names (mirrors app/auth/oidc.py's custom-claim test)", () => {
    const token = fakeToken({ sub: "admin@example.com", tenant: "acme2", groups: ["auditor"] });
    const principal = principalFromAccessToken(token, "tenant", "groups");
    expect(principal.organizationKey).toBe("acme2");
    expect(principal.roles).toEqual(new Set(["auditor"]));
  });

  it("throws when the organization claim is missing", () => {
    const token = fakeToken({ sub: "admin@example.com" });
    expect(() => principalFromAccessToken(token, "org", "roles")).toThrow();
  });

  it("throws when the organization claim is an empty string", () => {
    const token = fakeToken({ sub: "admin@example.com", org: "" });
    expect(() => principalFromAccessToken(token, "org", "roles")).toThrow();
  });

  it("throws on a malformed token", () => {
    expect(() => principalFromAccessToken("not-a-jwt", "org", "roles")).toThrow();
  });
});
