import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <p>Loading…</p>;
  }
  if (status === "signed-out") {
    // Router state carries `from` to the SignIn screen only (it cannot
    // survive the full navigation away to the IdP and back) -- SignIn
    // re-threads it into signIn()'s returnTo, which round-trips via
    // oidc-client-ts's own signin state instead.
    const from = `${location.pathname}${location.search}`;
    return <Navigate to="/signin" replace state={{ from }} />;
  }
  return <Outlet />;
}
