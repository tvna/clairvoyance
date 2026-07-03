import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { shouldRetryApiError } from "./api/client";
import { AuthProvider } from "./auth/AuthContext";
import { loadRuntimeConfig, type RuntimeConfig } from "./auth/config";
import { AppRoutes } from "./router";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Design §4/§8: every admin request is audited server-side and has
      // no rate limiting, so retries are bounded and status-aware
      // (shouldRetryApiError), and window-focus refetch is off.
      retry: shouldRetryApiError,
      refetchOnWindowFocus: false,
    },
  },
});

type BootState =
  | { status: "loading" }
  | { status: "ready"; config: RuntimeConfig }
  | { status: "error"; message: string };

export function App() {
  const [boot, setBoot] = useState<BootState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    loadRuntimeConfig()
      .then((config) => {
        if (!cancelled) {
          setBoot({ status: "ready", config });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setBoot({
            status: "error",
            message: error instanceof Error ? error.message : "failed to load configuration",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (boot.status === "loading") {
    return <p>Loading…</p>;
  }
  if (boot.status === "error") {
    return (
      <main>
        <h1>Configuration error</h1>
        <p>{boot.message}</p>
      </main>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider config={boot.config}>
        <BrowserRouter basename="/ui">
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
