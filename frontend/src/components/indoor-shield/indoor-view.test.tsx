import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { IndoorView } from "@/components/indoor-shield/indoor-view";
import { STORAGE_KEYS } from "@/features/store/storage";

describe("IndoorView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders every category and starts with an empty checklist", async () => {
    render(<IndoorView />);

    expect(await screen.findByText("0 of 8 complete")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ventilation" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dust" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Kitchen" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Filtration" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Clear checklist/ })).toBeDisabled();
  });

  it("records a completed action and clears the checklist", async () => {
    const user = userEvent.setup();
    render(<IndoorView />);

    const first = await screen.findByRole("checkbox", {
      name: "Keep windows closed during peak outdoor pollution",
    });
    await user.click(first);

    expect(screen.getByText("1 of 8 complete")).toBeInTheDocument();
    expect(screen.getByText("7 items remaining.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.indoorChecklist)).toContain(
      '"windows-closed-peak":true',
    );

    await user.click(screen.getByRole("button", { name: /Clear checklist/ }));

    expect(screen.getByText("0 of 8 complete")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.indoorChecklist)).toBeNull();
  });

  it("restores checked items from this browser", async () => {
    window.localStorage.setItem(
      STORAGE_KEYS.indoorChecklist,
      JSON.stringify({ "windows-closed-peak": true, "door-mats": true }),
    );
    render(<IndoorView />);

    expect(await screen.findByText("2 of 8 complete")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: "Keep windows closed during peak outdoor pollution" }),
    ).toBeChecked();
  });
});
