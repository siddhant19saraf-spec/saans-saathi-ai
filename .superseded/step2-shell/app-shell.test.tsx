import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import RouteError from "./error";
import Loading from "./loading";
import NotFound from "./not-found";
import HomePage from "./page";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("HomePage", () => {
  it("describes the release without claiming unimplemented features", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { level: 1, name: "SAANS SAATHI AI" })).toBeInTheDocument();
    expect(screen.getByText(/does not yet read air quality data/i)).toBeInTheDocument();
    expect(screen.getByText("Not implemented")).toBeInTheDocument();
  });
});

describe("NotFound", () => {
  it("offers a route back to the status page", () => {
    render(<NotFound />);

    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to project status" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});

describe("Loading", () => {
  it("exposes a busy status to assistive technology", () => {
    render(<Loading />);

    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Loading content")).toBeInTheDocument();
  });
});

describe("RouteError", () => {
  it("shows the digest and retries through the reset callback", async () => {
    const user = userEvent.setup();
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const reset = vi.fn();

    render(
      <RouteError error={Object.assign(new Error("boom"), { digest: "abc123" })} reset={reset} />,
    );

    expect(screen.getByText("Reference: abc123")).toBeInTheDocument();
    expect(consoleError).toHaveBeenCalledWith("Unhandled route error", "abc123");

    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("omits the reference block when no digest exists", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(<RouteError error={new Error("boom")} reset={vi.fn()} />);

    expect(screen.queryByText(/Reference:/)).not.toBeInTheDocument();
  });
});
