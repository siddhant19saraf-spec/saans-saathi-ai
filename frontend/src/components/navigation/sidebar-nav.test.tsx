import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { navGroups, allNavItems } from "./nav-config";
import { SidebarNav } from "./sidebar-nav";

const pathname = vi.hoisted(() => ({ current: "/dashboard" }));

vi.mock("next/navigation", () => ({
  usePathname: () => pathname.current,
}));

describe("SidebarNav", () => {
  it("renders every configured destination as a real link", () => {
    render(<SidebarNav />);
    const nav = screen.getByRole("navigation", { name: "Primary" });
    const links = within(nav).getAllByRole("link");
    expect(links).toHaveLength(allNavItems.length);

    for (const item of allNavItems) {
      expect(within(nav).getByRole("link", { name: item.label })).toHaveAttribute(
        "href",
        item.href,
      );
    }
  });

  it("marks the current route and only the current route", () => {
    pathname.current = "/dashboard";
    render(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Air intelligence" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("keeps the active state correct for nested routes", () => {
    pathname.current = "/family/members";
    render(<SidebarNav />);
    expect(screen.getByRole("link", { name: "Family intelligence" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("groups destinations under labelled sections", () => {
    render(<SidebarNav />);
    for (const group of navGroups) {
      expect(screen.getByRole("heading", { name: group.label })).toBeInTheDocument();
    }
  });
});
