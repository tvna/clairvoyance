import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CalibrationBar } from "../../src/components/CalibrationBar";

describe("CalibrationBar", () => {
  it("sizes segments against their own sum and shows unreported beside it (design §7.2)", () => {
    render(<CalibrationBar attempts={6} calibration={{ accurate: 3, overconfident: 1 }} />);
    expect(screen.getByText("2 unreported")).toBeInTheDocument();
    expect(screen.getByText(/accurate: 3/)).toBeInTheDocument();
    expect(screen.getByText(/overconfident: 1/)).toBeInTheDocument();
  });

  it("shows only the unreported count when every calibration value is unreported", () => {
    render(<CalibrationBar attempts={4} calibration={{}} />);
    expect(screen.getByText("4 unreported")).toBeInTheDocument();
  });

  it("omits the unreported line entirely when nothing is unreported", () => {
    render(<CalibrationBar attempts={2} calibration={{ accurate: 2 }} />);
    expect(screen.queryByText(/unreported/)).not.toBeInTheDocument();
  });
});
