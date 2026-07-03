import { useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface SignInLocationState {
  from?: string;
}

export function SignIn() {
  const { signIn, signOutNotice } = useAuth();
  const location = useLocation();
  const state = location.state as SignInLocationState | null;
  const returnTo = state?.from;

  return (
    <main>
      <h1>Clairvoyance Admin</h1>
      {signOutNotice !== null && <p role="status">{signOutNotice}</p>}
      <button type="button" onClick={() => void signIn(returnTo)}>
        Sign in
      </button>
    </main>
  );
}
