import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render } from "@testing-library/react";
import type { User, UserManager } from "oidc-client-ts";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../src/auth/AuthContext";
import type { RuntimeConfig } from "../../src/auth/config";
import { createUserManager } from "../../src/auth/oidcClient";

// The QueryClient is one long-lived instance above AuthProvider and admin
// query keys do not include the principal/organization, so a session ending
// (auth-expired, sign-out, or failed silent renew -- all routed through
// removeUser, which fires userUnloaded) must clear the cache, or the next
// organization to sign in could briefly render the previous org's cached data
// (retro #64, repair 5). This pins that the cache is empty immediately after
// userUnloaded fires, generalizing past the one instance that surfaced it.
vi.mock("../../src/auth/oidcClient", () => ({ createUserManager: vi.fn() }));

const config: RuntimeConfig = {
  issuer: "https://idp.example.com",
  client_id: "clairvoyance-ui",
  audience: "clairvoyance-managed",
  org_claim: "org",
  roles_claim: "roles",
};

/** A UserManager stub whose removeUser fires the userUnloaded event, exactly
 * as the real one does, exposed so the test can drive session end. */
function makeStubUserManager() {
  const unloaded: Array<() => void> = [];
  return {
    events: {
      addUserLoaded: (_cb: (user: User) => void) => () => {},
      addUserUnloaded: (cb: () => void) => {
        unloaded.push(cb);
        return () => {};
      },
    },
    getUser: async (): Promise<User | null> => null,
    signinSilent: async (): Promise<User | null> => null,
    removeUser: async (): Promise<void> => {
      for (const cb of unloaded) {
        cb();
      }
    },
    signinRedirect: async (): Promise<void> => {},
    signinCallback: async (): Promise<User> => ({}) as unknown as User,
    signoutRedirect: async (): Promise<void> => {},
  };
}

describe("cross-tenant query cache isolation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("clears the query cache immediately after userUnloaded fires", async () => {
    const userManager = makeStubUserManager();
    vi.mocked(createUserManager).mockReturnValue(userManager as unknown as UserManager);

    const queryClient = new QueryClient();
    // Stand in for a prior organization's cached admin data.
    queryClient.setQueryData(["contributors"], [{ id: "prev-org-contributor" }]);

    await act(async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider config={config}>
            <div />
          </AuthProvider>
        </QueryClientProvider>,
      );
    });

    // Sanity: the seeded data is present before the session ends.
    expect(queryClient.getQueryCache().getAll()).toHaveLength(1);

    // A session ending goes through removeUser -> userUnloaded.
    await act(async () => {
      await userManager.removeUser();
    });

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
  });
});
