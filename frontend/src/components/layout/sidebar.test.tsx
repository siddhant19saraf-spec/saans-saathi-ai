import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Sidebar } from "./sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

const STORAGE_KEY = "saans.v1.sidebarCollapsed";

describe("Sidebar", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts expanded and explains the data foundation", () => {
    render(<Sidebar />);

    expect(screen.getByText("Foundation build")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Expand sidebar" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review data sources" })).toHaveAttribute(
      "href",
      "/settings#data-sources",
    );
  });

  it("collapses on request and remembers the choice", async () => {
    const user = userEvent.setup();
    render(<Sidebar />);

    await user.click(screen.getByRole("button", { name: "Collapse sidebar" }));

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("true");
    expect(screen.queryByText("Foundation build")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Expand sidebar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Collapse sidebar" })).not.toBeInTheDocument();
  });

  it("restores a collapsed sidebar from storage", () => {
    window.localStorage.setItem(STORAGE_KEY, "true");
    render(<Sidebar />);

    expect(screen.getByRole("button", { name: "Expand sidebar" })).toBeInTheDocument();
    expect(screen.queryByText("Foundation build")).not.toBeInTheDocument();
  });

  it("expands again and persists the choice", async () => {
    window.localStorage.setItem(STORAGE_KEY, "true");
    const user = userEvent.setup();
    render(<Sidebar />);

    await user.click(screen.getByRole("button", { name: "Expand sidebar" }));

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("false");
    expect(screen.getByText("Foundation build")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toBeInTheDocument();
  });

  it("keeps the navigation available while collapsed", () => {
    window.localStorage.setItem(STORAGE_KEY, "true");
    render(<Sidebar />);

    const nav = screen.getByRole("navigation", { name: "Primary" });
    expect(within(nav).getAllByRole("link").length).toBeGreaterThan(0);
    expect(screen.getByTitle("CPCB 2014 AQI · anonymous family profile")).toBeInTheDocument();
  });

  it("renders the expanded footer trust statement", () => {
    render(<Sidebar />);

    expect(screen.getByText("CPCB 2014 AQI · anonymous family profile")).toBeInTheDocument();
    expect(screen.getByText("Every Breath Matters. Every Decision Counts.")).toBeInTheDocument();
  });

  it("defaults to expanded when storage cannot be read", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("storage blocked");
    });

    render(<Sidebar />);

    expect(screen.getByText("Foundation build")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("does not crash when storage cannot be written", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota exceeded");
    });
    const user = userEvent.setup();
    render(<Sidebar />);

    await user.click(screen.getByRole("button", { name: "Collapse sidebar" }));

    // The stored value stays absent, so the sidebar remains expanded rather
    // than pretending the preference was saved.
    expect(screen.getByText("Foundation build")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
