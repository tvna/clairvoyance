import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuditLogs } from "../../src/screens/AuditLogs";
import auditLogs from "../api/fixtures/audit_logs.json";
import { jsonResponse, renderWithProviders } from "../testUtils";

describe("AuditLogs screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders rows, the self-audit notice, and disables Next on a short page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, auditLogs)));

    renderWithProviders(<AuditLogs />);

    expect(await screen.findByText("list_contributors")).toBeInTheDocument();
    expect(
      screen.getByText("contributor:3f2b1a10-7c1e-4a4a-9b8a-6f2e1c9d0a11"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Viewing this screen writes an audit row of its own."),
    ).toBeInTheDocument();
    // Design §7.5: no `total` on this endpoint — a short page (2 rows,
    // page size 50) means no next page, never a wrong count.
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
});
