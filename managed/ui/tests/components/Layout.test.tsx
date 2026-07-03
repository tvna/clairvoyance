import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { Layout } from "../../src/components/Layout";
import { makeAuthState, renderWithProviders } from "../testUtils";

function renderLayout(roles: string[]) {
  return renderWithProviders(
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<p>content</p>} />
      </Route>
    </Routes>,
    {
      authState: makeAuthState({
        principal: {
          subject: "user@example.com",
          organizationKey: "acme",
          roles: new Set(roles as never[]),
        },
      }),
    },
  );
}

describe("Layout nav (design §2 — hiding is a courtesy, not a control)", () => {
  it("shows the audit logs link for org_admin", () => {
    renderLayout(["org_admin"]);
    expect(screen.getByRole("link", { name: "Audit logs" })).toBeInTheDocument();
  });

  it("hides the audit logs link for coach", () => {
    renderLayout(["coach"]);
    expect(screen.queryByRole("link", { name: "Audit logs" })).not.toBeInTheDocument();
    // Screens all roles can reach stay visible.
    expect(screen.getByRole("link", { name: "Contributors" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Policies" })).toBeInTheDocument();
  });
});
