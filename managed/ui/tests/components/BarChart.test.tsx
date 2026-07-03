import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BarChart } from "../../src/components/BarChart";

describe("BarChart", () => {
  it("omits zero-count categories and sorts by count descending", () => {
    render(
      <BarChart
        data={{ avoidance: 2, "loss-aversion": 5, "no-experiment": 0 }}
        ariaLabel="Events by category"
      />,
    );
    const svg = screen.getByRole("img", { name: "Events by category" });
    const labels = Array.from(svg.querySelectorAll("text")).map((node) => node.textContent);
    // "no experiment" (0 count) must not appear; "loss aversion" (5) before "avoidance" (2).
    expect(labels).not.toContain("no experiment");
    expect(labels.indexOf("loss aversion")).toBeLessThan(labels.indexOf("avoidance"));
  });

  it("shows an empty state when every category is zero", () => {
    render(<BarChart data={{ avoidance: 0 }} ariaLabel="Events by category" />);
    expect(screen.getByText("No events recorded.")).toBeInTheDocument();
  });
});
