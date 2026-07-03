import { User } from "oidc-client-ts";
import { beforeEach, describe, expect, it } from "vitest";
import type { RuntimeConfig } from "../../src/auth/config";
import { createUserManager } from "../../src/auth/oidcClient";

const config: RuntimeConfig = {
  issuer: "https://idp.example.com",
  client_id: "clairvoyance-ui",
  audience: "clairvoyance-managed",
  org_claim: "org",
  roles_claim: "roles",
};

function fakeAccessToken(): string {
  const header = btoa(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({ sub: "admin@example.com", org: "acme", roles: ["org_admin"] }),
  );
  return `${header}.${payload}.test-signature-marker-must-never-touch-web-storage`;
}

function allStorageValues(storage: Storage): string[] {
  const values: string[] = [];
  for (let i = 0; i < storage.length; i += 1) {
    const key = storage.key(i);
    if (key !== null) {
      values.push(storage.getItem(key) ?? "");
    }
  }
  return values;
}

describe("token storage pinning (design §5)", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  it("never writes the access or refresh token into sessionStorage or localStorage", async () => {
    // oidc-client-ts defaults userStore to window.sessionStorage
    // (UserManagerSettings.ts) — createUserManager must override this
    // explicitly to an in-memory store, or this test fails.
    const userManager = createUserManager(config);
    const accessToken = fakeAccessToken();
    const refreshToken = "test-refresh-token-marker-must-never-touch-web-storage";
    const nowSeconds = Math.floor(Date.now() / 1000);

    const user = new User({
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: "Bearer",
      profile: {
        sub: "admin@example.com",
        iss: config.issuer,
        aud: config.audience,
        exp: nowSeconds + 3600,
        iat: nowSeconds,
      },
      expires_at: nowSeconds + 3600,
    });

    // storeUser() is the exact code path oidc-client-ts uses to persist
    // tokens after any signin flow (redirect callback or silent renew via
    // refresh token) — this exercises the real configured userStore.
    await userManager.storeUser(user);

    for (const value of allStorageValues(window.sessionStorage)) {
      expect(value).not.toContain(accessToken);
      expect(value).not.toContain(refreshToken);
    }
    for (const value of allStorageValues(window.localStorage)) {
      expect(value).not.toContain(accessToken);
      expect(value).not.toContain(refreshToken);
    }

    // Round-trip sanity: the in-memory store still works as a real store.
    const reloaded = await userManager.getUser();
    expect(reloaded?.access_token).toBe(accessToken);
  });
});
