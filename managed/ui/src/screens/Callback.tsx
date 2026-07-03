import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Callback() {
  const { completeSignIn } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  // Runs once for the single redirect-back leg this screen exists for.
  // completeSignIn's identity changes when auth status flips (it closes
  // over status/principal), so including it would re-trigger the callback
  // exchange — a code+PKCE code can only be redeemed once.
  // biome-ignore lint/correctness/useExhaustiveDependencies: intentional run-once effect
  useEffect(() => {
    let cancelled = false;
    completeSignIn()
      .then(() => {
        if (!cancelled) {
          // Router basename is "/ui" (main.tsx), so app routes are
          // basename-relative.
          navigate("/", { replace: true });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "sign-in callback failed");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error !== null) {
    return (
      <main>
        <h1>Sign-in failed</h1>
        <p>{error}</p>
        <Link to="/signin">Try again</Link>
      </main>
    );
  }

  return (
    <main>
      <p>Signing in…</p>
    </main>
  );
}
