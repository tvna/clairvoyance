import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ContributorSummary } from "../../src/screens/ContributorSummary";
import contributorSummary from "../api/fixtures/contributor_summary.json";
import { jsonResponse, renderWithProviders } from "../testUtils";

const CONTRIBUTOR_ID = "3f2b1a10-7c1e-4a4a-9b8a-6f2e1c9d0a11";

function renderAtId(id: string) {
  return renderWithProviders(
    <Routes>
      <Route path="/contributors/:id" element={<ContributorSummary />} />
    </Routes>,
    { route: `/contributors/${id}` },
  );
}

describe("ContributorSummary screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the summary, categories, and the calibration unreported note", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, contributorSummary)));

    renderAtId(CONTRIBUTOR_ID);

    expect(await screen.findByRole("heading", { name: "tvna" })).toBeInTheDocument();
    expect(screen.getByText(/loss aversion/)).toBeInTheDocument();
    expect(screen.getByText(/6 attempts, 4 correct \(67%\)/)).toBeInTheDocument();
    // Fixture: attempts=6, calibration sums to 4 (3 accurate + 1 overconfident) — the
    // buckets do NOT partition attempts (design §7.2); must show 2 unreported, not
    // assert sum === attempts anywhere.
    expect(screen.getByText("2 unreported")).toBeInTheDocument();
  });

  it("shows 'no quiz attempts' instead of an empty chart when attempts is 0", async () => {
    const zeroQuiz = {
      ...contributorSummary,
      quiz: { attempts: 0, correct: 0, calibration: {} },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, zeroQuiz)));

    renderAtId(CONTRIBUTOR_ID);

    expect(await screen.findByText("No quiz attempts.")).toBeInTheDocument();
  });

  it("renders an in-place not-found state on 404, not a generic error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(404, { detail: "contributor not found" })),
    );

    renderAtId("00000000-0000-0000-0000-000000000000");

    expect(await screen.findByText("Contributor not found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to contributors" })).toHaveAttribute("href", "/");
  });
});
