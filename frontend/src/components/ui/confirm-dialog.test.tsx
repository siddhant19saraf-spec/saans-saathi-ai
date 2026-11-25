import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "./confirm-dialog";

describe("ConfirmDialog", () => {
  it("shows the title, description and default labels when open", () => {
    render(
      <ConfirmDialog
        open
        onOpenChange={vi.fn()}
        title="Delete activity?"
        description="This removes the activity from your log."
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Delete activity?")).toBeInTheDocument();
    expect(screen.getByText("This removes the activity from your log.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("renders nothing while closed", () => {
    render(
      <ConfirmDialog
        open={false}
        onOpenChange={vi.fn()}
        title="Delete activity?"
        description="Hidden"
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls onConfirm once when the confirm button is pressed", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        onOpenChange={vi.fn()}
        title="Clear log"
        description="Remove all entries."
        confirmLabel="Clear"
        onConfirm={onConfirm}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Clear" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("closes through onOpenChange when cancel is pressed", async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Clear log"
        description="Remove all entries."
        cancelLabel="Keep"
        onConfirm={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Keep" }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("disables the confirm button while busy", () => {
    render(
      <ConfirmDialog
        open
        onOpenChange={vi.fn()}
        title="Saving"
        description="Please wait."
        busy
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
  });
});
