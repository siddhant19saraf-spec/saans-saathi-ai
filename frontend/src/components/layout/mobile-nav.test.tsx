import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MobileNav } from "@/components/layout/mobile-nav";

const pathname = vi.hoisted(() => ({ current: "/smart-routine" }));

vi.mock("next/navigation", () => ({
  usePathname: () => pathname.current,
}));

describe("MobileNav", () => {
  it("opens a labelled navigation dialog from the menu button", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    await user.click(screen.getByRole("button", { name: "Open navigation menu" }));

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Navigation")).toBeInTheDocument();
    expect(within(dialog).getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
  });

  it("shows the active route inside the mobile menu", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    await user.click(screen.getByRole("button", { name: "Open navigation menu" }));
    const dialog = await screen.findByRole("dialog");

    expect(within(dialog).getByRole("link", { name: "SmartRoutine" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("closes the dialog from the close control", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);

    await user.click(screen.getByRole("button", { name: "Open navigation menu" }));
    await screen.findByRole("dialog");

    await user.click(screen.getByRole("button", { name: "Close dialog" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });
});
