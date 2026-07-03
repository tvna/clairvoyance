import { InMemoryWebStorage, UserManager, WebStorageStateStore } from "oidc-client-ts";
import type { RuntimeConfig } from "./config";

export function createUserManager(config: RuntimeConfig): UserManager {
  const redirectUri = `${window.location.origin}/ui/callback`;
  const postLogoutRedirectUri = `${window.location.origin}/ui/`;

  const metadataSeed: Record<string, string> = {};
  if (config.authorization_endpoint !== undefined) {
    metadataSeed.authorization_endpoint = config.authorization_endpoint;
  }
  if (config.token_endpoint !== undefined) {
    metadataSeed.token_endpoint = config.token_endpoint;
  }
  if (config.end_session_endpoint !== undefined) {
    metadataSeed.end_session_endpoint = config.end_session_endpoint;
  }
  const hasOverrides = Object.keys(metadataSeed).length > 0;

  return new UserManager({
    authority: config.issuer,
    client_id: config.client_id,
    redirect_uri: redirectUri,
    post_logout_redirect_uri: postLogoutRedirectUri,
    response_type: "code",
    scope: "openid profile offline_access",
    // Overrides only the given endpoints via metadataSeed (merged on top of
    // the fetched discovery document) rather than `metadata` (which would
    // skip discovery entirely and drop issuer/jwks_uri) — providers publish
    // authorize/token/end-session endpoints at non-standard paths sometimes,
    // mirroring the server's own explicit-JWKS-URL rationale (app/auth/
    // oidc.py).
    ...(hasOverrides ? { metadataSeed } : {}),
    // Common convention for requesting an access token scoped to a
    // specific resource server (Auth0-style `audience`); deployments whose
    // provider uses a different mechanism (e.g. `resource`) are a
    // per-provider registration detail, documented in the PR.
    extraQueryParams: { audience: config.audience },
    // Design §5: explicit override of the sessionStorage default. Tokens
    // must never reach web storage — tests/auth/tokenStorage.test.ts pins
    // this. The redirect interaction state (stateStore: nonce/PKCE
    // verifier) stays on its window.localStorage default: it carries no
    // tokens and the library clears it on callback.
    userStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
    automaticSilentRenew: true,
    // No silent_redirect_uri is set anywhere in this config: with it unset,
    // signinSilent() throws "No silent_redirect_uri configured" instead of
    // falling back to an iframe when no refresh_token is present. Renewal
    // is refresh-token-only by construction, matching the CSP's absent
    // frame-src (design §5/§9).
  });
}
