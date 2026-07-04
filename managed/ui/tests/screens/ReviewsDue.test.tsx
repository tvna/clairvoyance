import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReviewsDue } from "../../src/screens/ReviewsDue";
import { jsonResponse, makeAuthState, renderWithProviders } from "../testUtils";

const SCHEDULE_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d";
const CONTRIBUTOR_ID = "3f2b1a10-7c1e-4a4a-9b8a-6f2e1c9d0a11";
const DAY_MS = 24 * 60 * 60 * 1000;

function isoDaysAgo(days: number): string {
  return new Date(Date.now() - days * DAY_MS).toISOString();
}

function dueRow(overrides: Record<string, unknown> = {}) {
  return {
    id: SCHEDULE_ID,
    contributor_id: CONTRIBUTOR_ID,
    display_name: "octocat",
    provider: "github",
    external_id: "12345678",
    category: "avoidance",
    signal: null,
    due_at: isoDaysAgo(3),
    interval_days: 3,
    last_outcome: "correct",
    ...overrides,
  };
}

describe("ReviewsDue screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the contributor identity straight from the row (no client-side join)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { due: [dueRow()] })));

    renderWithProviders(<ReviewsDue />);

    expect(await screen.findByText(/Overdue by 3 days/)).toBeInTheDocument();
    // The name comes from the row's display_name, not a cached lookup, and the
    // one request the screen makes is to /v1/admin/reviews/due.
    expect(screen.getByRole("link", { name: "octocat" })).toHaveAttribute(
      "href",
      `/contributors/${CONTRIBUTOR_ID}`,
    );
  });

  it("falls back to provider:external_id when display_name is null", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { due: [dueRow({ display_name: null })] })),
    );

    renderWithProviders(<ReviewsDue />);

    expect(await screen.findByRole("link", { name: "github:12345678" })).toBeInTheDocument();
  });

  it("shows the success empty state when nothing is due", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { due: [] })));

    renderWithProviders(<ReviewsDue />);

    expect(await screen.findByText("No reviews due.")).toBeInTheDocument();
  });

  it("hides the dismiss action for a role without dismiss rights (auditor)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { due: [dueRow()] })));

    renderWithProviders(<ReviewsDue />, {
      authState: makeAuthState({
        principal: {
          subject: "auditor@example.com",
          organizationKey: "acme",
          roles: new Set(["auditor"]),
        },
      }),
    });

    await screen.findByText(/Overdue by 3 days/);
    expect(screen.queryByRole("button", { name: "Dismiss" })).not.toBeInTheDocument();
  });

  it("dismisses a row after confirmation and posts to the dismiss endpoint (coach)", async () => {
    const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "POST") {
        return Promise.resolve(
          jsonResponse(200, {
            id: SCHEDULE_ID,
            status: "dismissed",
            dismissed_at: new Date().toISOString(),
            dismissed_by: "coach@example.com",
          }),
        );
      }
      return Promise.resolve(jsonResponse(200, { due: [dueRow()] }));
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderWithProviders(<ReviewsDue />, {
      authState: makeAuthState({
        principal: {
          subject: "coach@example.com",
          organizationKey: "acme",
          roles: new Set(["coach"]),
        },
      }),
    });

    await user.click(await screen.findByRole("button", { name: "Dismiss" }));

    // A confirmation dialog gates the write (design §7.3).
    const dialog = screen.getByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      const postCall = fetchMock.mock.calls.find(
        ([, init]) => (init as RequestInit | undefined)?.method === "POST",
      );
      expect(postCall?.[0]).toBe(`/v1/admin/reviews/${SCHEDULE_ID}/dismiss`);
    });
    // The dialog closes on success.
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});
