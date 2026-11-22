import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("links the brand name to the home page", () => {
    render(<SiteHeader />);

    const brand = screen.getByRole("link", { name: "SAANS SAATHI AI" });
    expect(brand).toHaveAttribute("href", "/");
  });

  it("marks the build as a foundation release", () => {
    render(<SiteHeader />);

    expect(screen.getByText("Foundation build")).toBeInTheDocument();
  });
});
