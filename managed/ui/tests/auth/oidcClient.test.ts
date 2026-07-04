import { describe, expect, it } from "vitest";
import type { RuntimeConfig } from "../../src/auth/config";
import { createUserManager } from "../../src/auth/oidcClient";

// oidc-client-ts's MetadataService only merges `metadataSeed` after a
// successful discovery fetch, so a provider with no discovery document would
// fail sign-in before an endpoint override ever applied (retro #64, repair 2).
// createUserManager must therefore build a full `metadata` object (which skips
// discovery outright) when both endpoints every sign-in/token call needs are
// overridden, and fall back to `metadataSeed` only for a genuinely partial
// override that still relies on discovery for the rest.
const baseConfig: RuntimeConfig = {
  issuer: "https://idp.example.com",
  client_id: "clairvoyance-ui",
  audience: "clairvoyance-managed",
  org_claim: "org",
  roles_claim: "roles",
};

const AUTHORIZATION_ENDPOINT = "https://idp.example.com/oauth/authorize";
const TOKEN_ENDPOINT = "https://idp.example.com/oauth/token";
const END_SESSION_ENDPOINT = "https://idp.example.com/oauth/logout";

describe("createUserManager metadata handling", () => {
  it("builds a full metadata object and skips discovery when both endpoints are overridden", () => {
    const manager = createUserManager({
      ...baseConfig,
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
      token_endpoint: TOKEN_ENDPOINT,
    });

    expect(manager.settings.metadata).toEqual({
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
      token_endpoint: TOKEN_ENDPOINT,
    });
    expect(manager.settings.metadataSeed).toBeUndefined();
  });

  it("folds a same-request end_session override into the full metadata object", () => {
    const manager = createUserManager({
      ...baseConfig,
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
      token_endpoint: TOKEN_ENDPOINT,
      end_session_endpoint: END_SESSION_ENDPOINT,
    });

    expect(manager.settings.metadata).toEqual({
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
      token_endpoint: TOKEN_ENDPOINT,
      end_session_endpoint: END_SESSION_ENDPOINT,
    });
    expect(manager.settings.metadataSeed).toBeUndefined();
  });

  it("uses metadataSeed (keeping discovery) for a partial override missing token_endpoint", () => {
    const manager = createUserManager({
      ...baseConfig,
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
    });

    expect(manager.settings.metadata).toBeUndefined();
    expect(manager.settings.metadataSeed).toEqual({
      authorization_endpoint: AUTHORIZATION_ENDPOINT,
    });
  });

  it("uses metadataSeed for an end_session-only override, since discovery must still supply the endpoints", () => {
    const manager = createUserManager({
      ...baseConfig,
      end_session_endpoint: END_SESSION_ENDPOINT,
    });

    expect(manager.settings.metadata).toBeUndefined();
    expect(manager.settings.metadataSeed).toEqual({
      end_session_endpoint: END_SESSION_ENDPOINT,
    });
  });

  it("passes neither metadata nor metadataSeed when nothing is overridden", () => {
    const manager = createUserManager(baseConfig);

    expect(manager.settings.metadata).toBeUndefined();
    expect(manager.settings.metadataSeed).toBeUndefined();
  });
});
