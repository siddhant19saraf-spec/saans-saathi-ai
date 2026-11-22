import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteFooter } from "./site-footer";
import { SkipLink } from "./skip-link";

describe("SkipLink", () => {
  it("targets the main landmark", () => {
    render(<SkipLink />);

    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
  });
});

describe("SiteFooter", () => {
  it("states that air quality guidance is unavailable", () => {
    render(<SiteFooter />);

    expect(
      screen.getByText(/Air quality guidance is not available in this build/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/will state their data source/i)).toBeInTheDocument();
  });
});
