import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Contributors } from "../../src/screens/Contributors";
import contributorList from "../api/fixtures/contributor_list.json";
import { jsonResponse, renderWithProviders } from "../testUtils";

describe("Contributors screen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the contributor table with the total and a link to the summary", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, contributorList)));

    renderWithProviders(<Contributors />);

    expect(await screen.findByText("tvna")).toBeInTheDocument();
    // Fallback display name when null (design §7.1).
    expect(screen.getByText("github:99887766")).toBeInTheDocument();
    expect(screen.getByText("2 total")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "tvna" })).toHaveAttribute(
      "href",
      "/contributors/3f2b1a10-7c1e-4a4a-9b8a-6f2e1c9d0a11",
    );
    // offset(0) + limit(50) >= total(2): no next page.
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("shows the onboarding empty state when there are no contributors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { contributors: [], total: 0 })),
    );

    renderWithProviders(<Contributors />);

    expect(await screen.findByText(/Mint a collector token/)).toBeInTheDocument();
  });

  it("renders the forbidden view on a 403", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(403, { detail: "insufficient role" })),
    );

    renderWithProviders(<Contributors />);

    expect(await screen.findByText("Access denied")).toBeInTheDocument();
    expect(screen.getByText(/view contributors/)).toBeInTheDocument();
  });
});
