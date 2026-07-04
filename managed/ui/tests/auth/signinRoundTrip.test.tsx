import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { User, UserManager } from "oidc-client-ts";
import { MemoryRouter, type NavigateFunction, useLocation, useNavigate } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../src/auth/AuthContext";
import type { RuntimeConfig } from "../../src/auth/config";
import { createUserManager } from "../../src/auth/oidcClient";
import { AppRoutes } from "../../src/router";

// The return-to-original-path behavior is an integration across a full
// redirect round trip -- RequireAuth captures the requested path, SignIn
// re-threads it into signIn(), it round-trips through the provider as
// oidc-client-ts signin `state`, and Callback navigates back to it. Component
// tests that inject a pre-signed-in AuthState structurally cannot exercise it
// (retro #64, repair 3), so this test drives the real AuthProvider against a
// stub UserManager and asserts sign-in from a protected route lands back on
// that route, not on "/".
vi.mock("../../src/auth/oidcClient", () => ({ createUserManager: vi.fn() }));

const config: RuntimeConfig = {
  issuer: "https://idp.example.com",
  client_id: "clairvoyance-ui",
  audience: "clairvoyance-managed",
  org_claim: "org",
  roles_claim: "roles",
};

function base64Url(value: unknown): string {
  return btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// A decodable (unsigned) access token carrying the org/roles claims
// principalFromAccessToken reads; the SPA never verifies the signature.
const ACCESS_TOKEN = `${base64Url({ alg: "none" })}.${base64Url({
  sub: "e2e-admin@example.com",
  org: "acme",
  roles: ["org_admin"],
})}.signature`;

/** A minimal UserManager standing in for oidc-client-ts: it records the signin
 * `state` on redirect and replays it (plus a valid user) on callback, firing
 * the userLoaded event AuthProvider subscribes to. */
function makeStubUserManager(): UserManager {
  const loaded: Array<(user: User) => void> = [];
  const unloaded: Array<() => void> = [];
  let capturedState: string | undefined;

  const stub = {
    events: {
      addUserLoaded: (cb: (user: User) => void) => {
        loaded.push(cb);
        return () => {};
      },
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
    signinRedirect: async (args?: { state?: string }): Promise<void> => {
      capturedState = args?.state;
    },
    signinCallback: async (): Promise<User> => {
      const user = { access_token: ACCESS_TOKEN, state: capturedState } as unknown as User;
      for (const cb of loaded) {
        cb(user);
      }
      return user;
    },
    signoutRedirect: async (): Promise<void> => {},
  };
  return stub as unknown as UserManager;
}

let capturedNavigate: NavigateFunction | null = null;

function NavProbe() {
  capturedNavigate = useNavigate();
  const location = useLocation();
  return <div data-testid="pathname">{location.pathname}</div>;
}

describe("sign-in round trip", () => {
  beforeEach(() => {
    capturedNavigate = null;
    vi.mocked(createUserManager).mockReturnValue(makeStubUserManager());
    // The protected screen mounts once we return to it and fires admin
    // queries; a benign stub keeps them off the real network.
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response("[]", { headers: { "content-type": "application/json" } })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("returns to the originally requested path after signing in", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider config={config}>
          <MemoryRouter initialEntries={["/policies"]}>
            <NavProbe />
            <AppRoutes />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>,
    );

    // Unauthenticated request to /policies redirects to the sign-in screen.
    const signInButton = await screen.findByRole("button", { name: "Sign in" });

    // Signing in records the return path as the provider signin `state`.
    await userEvent.click(signInButton);

    // Simulate the provider redirecting the browser back to the callback route.
    expect(capturedNavigate).not.toBeNull();
    act(() => {
      capturedNavigate?.("/callback");
    });

    // The callback replays the state and navigates back to /policies, not "/".
    await waitFor(() => {
      expect(screen.getByTestId("pathname")).toHaveTextContent("/policies");
    });
  });
});
