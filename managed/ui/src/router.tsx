import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { AuditLogs } from "./screens/AuditLogs";
import { Callback } from "./screens/Callback";
import { ContributorSummary } from "./screens/ContributorSummary";
import { Contributors } from "./screens/Contributors";
import { Policies } from "./screens/Policies";
import { ReviewsDue } from "./screens/ReviewsDue";
import { SignIn } from "./screens/SignIn";

// Paths are relative to the router's basename ("/ui", set in main.tsx).
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/signin" element={<SignIn />} />
      <Route path="/callback" element={<Callback />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<Contributors />} />
          <Route path="contributors/:id" element={<ContributorSummary />} />
          <Route path="reviews" element={<ReviewsDue />} />
          <Route path="policies" element={<Policies />} />
          <Route path="audit" element={<AuditLogs />} />
        </Route>
      </Route>
    </Routes>
  );
}
