import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function RequireAuth() {
  const { status } = useAuth();

  if (status === "loading") {
    return <p>Loading…</p>;
  }
  if (status === "signed-out") {
    return <Navigate to="/signin" replace />;
  }
  return <Outlet />;
}
