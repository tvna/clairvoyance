import { InMemoryWebStorage, UserManager, WebStorageStateStore } from "oidc-client-ts";
import type { RuntimeConfig } from "./config";

export function createUserManager(config: RuntimeConfig): UserManager {
  const redirectUri = `${window.location.origin}/ui/callback`;
  const postLogoutRedirectUri = `${window.location.origin}/ui/`;

  // oidc-client-ts's MetadataService only merges metadataSeed AFTER a
  // successful discovery fetch (getMetadata(): fetch metadataUrl, then
  // Object.assign(fetched, metadataSeed)) -- if discovery itself is
  // unreachable, metadataSeed never applies and signin fails outright.
  // authorization_endpoint and token_endpoint are the two fields every
  // signin/token-exchange call actually needs (this SPA never calls
  // getIssuer()/getUserInfoEndpoint(), and does no client-side JWKS/
  // signature verification, so issuer/jwks_uri from the discovery
  // document are not required here). When both are present, build a
  // full `metadata` object and skip discovery entirely -- the only way
  // to genuinely support "discovery document is absent" (design §6).
  // A partial override (e.g. only end_session_endpoint, because a
  // provider's discovery omits just that field while still publishing
  // the rest) keeps using metadataSeed, since discovery must still
  // supply the fields that were not overridden.
  const hasAuthorizationOverride = config.authorization_endpoint !== undefined;
  const hasTokenOverride = config.token_endpoint !== undefined;
  const canSkipDiscovery = hasAuthorizationOverride && hasTokenOverride;

  const fullMetadata: Record<string, string> = {};
  const metadataSeed: Record<string, string> = {};
  if (config.authorization_endpoint !== undefined) {
    (canSkipDiscovery ? fullMetadata : metadataSeed).authorization_endpoint =
      config.authorization_endpoint;
  }
  if (config.token_endpoint !== undefined) {
    (canSkipDiscovery ? fullMetadata : metadataSeed).token_endpoint = config.token_endpoint;
  }
  if (config.end_session_endpoint !== undefined) {
    (canSkipDiscovery ? fullMetadata : metadataSeed).end_session_endpoint =
      config.end_session_endpoint;
  }

  return new UserManager({
    authority: config.issuer,
    client_id: config.client_id,
    redirect_uri: redirectUri,
    post_logout_redirect_uri: postLogoutRedirectUri,
    response_type: "code",
    scope: "openid profile offline_access",
    ...(canSkipDiscovery ? { metadata: fullMetadata } : {}),
    ...(!canSkipDiscovery && Object.keys(metadataSeed).length > 0 ? { metadataSeed } : {}),
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
