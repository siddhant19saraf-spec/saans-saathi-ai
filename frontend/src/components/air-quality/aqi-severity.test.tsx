import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AqiDial } from "./aqi-dial";
import { SeverityBadge } from "./severity-badge";

describe("SeverityBadge", () => {
  it("names the category in text, not only in colour", () => {
    render(<SeverityBadge category="poor" showRange />);
    expect(screen.getByText("Poor")).toBeInTheDocument();
    expect(screen.getByText(/AQI 201–300/)).toBeInTheDocument();
  });

  it("reports an unavailable AQI instead of inventing a category", () => {
    render(<SeverityBadge category={null} />);
    expect(screen.getByText("AQI unavailable")).toBeInTheDocument();
  });
});

describe("AqiDial", () => {
  it("shows a dash and an explicit label when no reading exists", () => {
    render(<AqiDial value={null} category={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("No reading")).toBeInTheDocument();
    expect(screen.getByRole("img")).toHaveAccessibleName("CPCB AQI is unavailable");
  });

  it("describes the value and CPCB category for assistive technology", () => {
    render(<AqiDial value={245.4} category="poor" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("CPCB AQI 245, Poor category");
    expect(screen.getByText("245")).toBeInTheDocument();
  });
});
