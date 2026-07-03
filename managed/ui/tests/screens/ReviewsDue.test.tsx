import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReviewsDue } from "../../src/screens/ReviewsDue";
import { jsonResponse, renderWithProviders } from "../testUtils";

const CONTRIBUTOR_ID = "3f2b1a10-7c1e-4a4a-9b8a-6f2e1c9d0a11";
const DAY_MS = 24 * 60 * 60 * 1000;

function isoDaysAgo(days: number): string {
  return new Date(Date.now() - days * DAY_MS).toISOString();
}

describe("ReviewsDue screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a shortened contributor id when nothing is cached from Contributors (design §7.3)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(200, {
          due: [
            {
              contributor_id: CONTRIBUTOR_ID,
              category: "avoidance",
              signal: null,
              due_at: isoDaysAgo(3),
              interval_days: 3,
              last_outcome: "correct",
            },
          ],
        }),
      ),
    );

    renderWithProviders(<ReviewsDue />);

    expect(await screen.findByText(/Overdue by 3 days/)).toBeInTheDocument();
    // No per-row summary call is made — this screen only issues one
    // request, to /v1/admin/reviews/due (design §7.3).
    expect(screen.getByRole("link", { name: `${CONTRIBUTOR_ID.slice(0, 8)}…` })).toHaveAttribute(
      "href",
      `/contributors/${CONTRIBUTOR_ID}`,
    );
  });

  it("shows the success empty state when nothing is due", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { due: [] })));

    renderWithProviders(<ReviewsDue />);

    expect(await screen.findByText("No reviews due.")).toBeInTheDocument();
  });
});
