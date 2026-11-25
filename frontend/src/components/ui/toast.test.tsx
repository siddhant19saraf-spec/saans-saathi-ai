import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToastProvider, useToast } from "./toast";

function Trigger({ message, tone }: { message: string; tone?: "success" | "info" | "error" }) {
  const { notify } = useToast();
  return (
    <button type="button" onClick={() => notify(message, tone)}>
      Notify
    </button>
  );
}

describe("ToastProvider", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders its children", () => {
    render(
      <ToastProvider>
        <p>Workspace content</p>
      </ToastProvider>,
    );
    expect(screen.getByText("Workspace content")).toBeInTheDocument();
  });

  it("throws a clear error when the hook is used outside the provider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Trigger message="nope" />)).toThrow(
      "useToast must be used inside ToastProvider.",
    );
    spy.mockRestore();
  });

  it("shows a notification when notify is called", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <Trigger message="Location saved" />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Notify" }));

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Location saved");
  });

  it("dismisses a notification through its accessible button", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <Trigger message="Dismiss me" tone="info" />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Notify" }));
    expect(screen.getByText("Dismiss me")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Dismiss notification" }));
    expect(screen.queryByText("Dismiss me")).not.toBeInTheDocument();
  });

  it("auto-dismisses after the display window", () => {
    vi.useFakeTimers();
    render(
      <ToastProvider>
        <Trigger message="Transient" tone="error" />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Notify" }));
    expect(screen.getByText("Transient")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4500);
    });
    expect(screen.queryByText("Transient")).not.toBeInTheDocument();
  });

  it("keeps at most three notifications visible", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <Trigger message="First" />
      </ToastProvider>,
    );

    const button = screen.getByRole("button", { name: "Notify" });
    await user.click(button);
    await user.click(button);
    await user.click(button);
    await user.click(button);

    expect(screen.getAllByRole("status")).toHaveLength(3);
  });
});
