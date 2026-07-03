import type { User, UserManager } from "oidc-client-ts";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { configureApiAuth } from "../api/client";
import type { RuntimeConfig } from "./config";
import { createUserManager } from "./oidcClient";
import { type AdminPrincipal, principalFromAccessToken } from "./principal";

export type AuthStatus = "loading" | "signed-out" | "signed-in";

export interface AuthState {
  status: AuthStatus;
  principal: AdminPrincipal | null;
  /** Set after a sign-out when the provider advertises no end-session endpoint (design §5). */
  signOutNotice: string | null;
  /** `returnTo` round-trips through the provider via oidc-client-ts's own
   * signin `state` (not router state, which cannot survive a full
   * navigation away to the IdP and back). */
  signIn: (returnTo?: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Completes the redirect-back leg of the code+PKCE flow (Callback
   * screen only). Resolves the `returnTo` path passed to signIn(), if any. */
  completeSignIn: () => Promise<string | undefined>;
}

// Exported (not just AuthProvider/useAuth) so tests can inject a fake
// AuthState without booting real oidc-client-ts wiring.
export const AuthReactContext = createContext<AuthState | null>(null);

const NO_END_SESSION_NOTICE =
  "Your tokens were dropped locally, but this provider has no end-session endpoint, so your provider session may still be active. Signing back in may not prompt for credentials.";

const SIGN_OUT_FAILED_NOTICE =
  "Your tokens were dropped locally, but the sign-out redirect to the provider failed, so your provider session may still be active.";

// oidc-client-ts (pinned 3.5.x) throws exactly this message from
// createSignoutRequest when the provider metadata lacks end_session_endpoint.
const NO_END_SESSION_ERROR_MESSAGE = "No end session endpoint";

function derivePrincipal(user: User | null, config: RuntimeConfig): AdminPrincipal | null {
  if (user === null) {
    return null;
  }
  return principalFromAccessToken(user.access_token, config.org_claim, config.roles_claim);
}

export function AuthProvider({ config, children }: { config: RuntimeConfig; children: ReactNode }) {
  const userManager = useMemo<UserManager>(() => createUserManager(config), [config]);
  const userRef = useRef<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [principal, setPrincipal] = useState<AdminPrincipal | null>(null);
  const [signOutNotice, setSignOutNotice] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function attemptSilentRenewOrSignOut(): Promise<boolean> {
      try {
        const renewed = await userManager.signinSilent();
        if (renewed === null) {
          return false;
        }
        userRef.current = renewed;
        setPrincipal(derivePrincipal(renewed, config));
        return true;
      } catch {
        await userManager.removeUser();
        userRef.current = null;
        setPrincipal(null);
        setStatus("signed-out");
        return false;
      }
    }

    configureApiAuth({
      getAccessToken: () => userRef.current?.access_token ?? null,
      onUnauthorized: attemptSilentRenewOrSignOut,
      // removeUser fires addUserUnloaded (below), flipping status to
      // signed-out so RequireAuth performs the redirect the
      // AuthExpiredError copy promises.
      onAuthExpired: async () => {
        await userManager.removeUser();
      },
    });

    const unsubscribeLoaded = userManager.events.addUserLoaded((user) => {
      // Derive the principal before adopting the token: a token missing
      // the org/roles claim must not become the active token while the
      // screen keeps showing the previous principal. Signing out fails
      // loudly (addUserUnloaded resets state); rethrowing keeps the
      // Callback screen's sign-in error path intact.
      let nextPrincipal: AdminPrincipal | null;
      try {
        nextPrincipal = derivePrincipal(user, config);
      } catch (error) {
        void userManager.removeUser();
        throw error;
      }
      userRef.current = user;
      setPrincipal(nextPrincipal);
      setStatus("signed-in");
    });
    const unsubscribeUnloaded = userManager.events.addUserUnloaded(() => {
      userRef.current = null;
      setPrincipal(null);
      setStatus("signed-out");
    });

    userManager
      .getUser()
      .then((user) => {
        if (cancelled) {
          return;
        }
        if (user !== null && !user.expired) {
          userRef.current = user;
          setPrincipal(derivePrincipal(user, config));
          setStatus("signed-in");
        } else {
          setStatus("signed-out");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("signed-out");
        }
      });

    return () => {
      cancelled = true;
      unsubscribeLoaded();
      unsubscribeUnloaded();
    };
  }, [userManager, config]);

  const value = useMemo<AuthState>(
    () => ({
      status,
      principal,
      signOutNotice,
      signIn: (returnTo) =>
        userManager.signinRedirect(returnTo !== undefined ? { state: returnTo } : {}),
      completeSignIn: async () => {
        // addUserLoaded (subscribed above) picks up the resulting user and
        // flips status to signed-in; the Callback screen just awaits this
        // to know when to navigate away (success or failure). The signin
        // `state` (set by signIn's returnTo) round-trips on the User.
        const user = await userManager.signinCallback();
        return typeof user?.state === "string" ? user.state : undefined;
      },
      signOut: async () => {
        setSignOutNotice(null);
        try {
          // Drops server-side session at the provider when it advertises
          // end-session; also removes the local user as part of the flow.
          await userManager.signoutRedirect();
        } catch (error) {
          await userManager.removeUser();
          if (error instanceof Error && error.message === NO_END_SESSION_ERROR_MESSAGE) {
            // No end-session endpoint (design §5): dropping local tokens
            // does not end the provider's SSO session.
            setSignOutNotice(NO_END_SESSION_NOTICE);
          } else {
            // Any other failure (metadata fetch, malformed endpoint, …)
            // must not masquerade as the known provider limitation.
            console.error("sign-out redirect failed", error);
            setSignOutNotice(SIGN_OUT_FAILED_NOTICE);
          }
        }
      },
    }),
    [status, principal, signOutNotice, userManager],
  );

  return <AuthReactContext.Provider value={value}>{children}</AuthReactContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthReactContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
