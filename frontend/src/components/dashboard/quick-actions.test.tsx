import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QuickActions } from "./quick-actions";

describe("QuickActions", () => {
  it("renders a labelled section with all four destinations", () => {
    render(<QuickActions />);

    const section = screen.getByRole("region", { name: "Quick actions" });
    expect(within(section).getByText("Jump straight into the workspace you need.")).toBeInTheDocument();

    const links = within(section).getAllByRole("link");
    expect(links).toHaveLength(4);
  });

  it("links each action to its workspace route", () => {
    render(<QuickActions />);

    const expected: Array<[string, string]> = [
      ["/air-quality", "Air intelligence"],
      ["/family", "Family intelligence"],
      ["/smart-routine", "SmartRoutine"],
      ["/impact", "Impact log"],
    ];

    for (const [href, label] of expected) {
      const link = screen.getByRole("link", { name: new RegExp(label, "i") });
      expect(link).toHaveAttribute("href", href);
    }
  });

  it("describes what each action does", () => {
    render(<QuickActions />);

    expect(screen.getByText("Pollutants, source and forecast")).toBeInTheDocument();
    expect(screen.getByText("Household profile and consent")).toBeInTheDocument();
    expect(screen.getByText("Plan around lower-exposure hours")).toBeInTheDocument();
    expect(screen.getByText("Record low-carbon actions")).toBeInTheDocument();
  });
});
