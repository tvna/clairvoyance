import { useAuth } from "../auth/AuthContext";

export function SignIn() {
  const { signIn, signOutNotice } = useAuth();

  return (
    <main>
      <h1>Clairvoyance Admin</h1>
      {signOutNotice !== null && <p role="status">{signOutNotice}</p>}
      <button type="button" onClick={() => void signIn()}>
        Sign in
      </button>
    </main>
  );
}
