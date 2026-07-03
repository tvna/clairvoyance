import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { AuthReactContext, type AuthState } from "../src/auth/AuthContext";
import type { Role } from "../src/auth/roles";

export function makeAuthState(overrides: Partial<AuthState> = {}): AuthState {
  return {
    status: "signed-in",
    principal: {
      subject: "admin@example.com",
      organizationKey: "acme",
      roles: new Set<Role>(["org_admin"]),
    },
    signOutNotice: null,
    signIn: async () => {},
    signOut: async () => {},
    completeSignIn: async () => {},
    ...overrides,
  };
}

/** Renders a screen with a fresh (non-retrying) QueryClient, a fake auth
 * context (no real oidc-client-ts wiring needed), and a MemoryRouter. */
export function renderWithProviders(
  ui: ReactElement,
  { authState = makeAuthState(), route = "/" }: { authState?: AuthState; route?: string } = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthReactContext.Provider value={authState}>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </AuthReactContext.Provider>
    </QueryClientProvider>,
  );
}

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
