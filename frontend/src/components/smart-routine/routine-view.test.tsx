import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { RoutineView } from "@/components/smart-routine/routine-view";
import { STORAGE_KEYS } from "@/features/store/storage";

describe("RoutineView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts empty and says that timing guidance is not connected", async () => {
    render(<RoutineView />);

    expect(await screen.findByText("No activities yet")).toBeInTheDocument();
    expect(screen.getByText("Timing guidance is not connected")).toBeInTheDocument();
    expect(screen.getByText("0 of 12 activities")).toBeInTheDocument();
  });

  it("adds an activity with its computed end time and removes it", async () => {
    const user = userEvent.setup();
    render(<RoutineView />);

    await user.type(await screen.findByLabelText("Activity"), "Morning walk");
    await user.click(screen.getByRole("button", { name: /Add to routine/ }));

    expect(screen.getByRole("heading", { name: "Morning" })).toBeInTheDocument();
    expect(screen.getByText("07:00")).toBeInTheDocument();
    expect(screen.getByText("to 07:30")).toBeInTheDocument();
    expect(screen.getAllByText("Outdoors").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Moderate").length).toBeGreaterThan(0);
    expect(window.localStorage.getItem(STORAGE_KEYS.routineActivities)).toContain("Morning walk");

    await user.click(screen.getByRole("button", { name: "Remove Morning walk" }));

    expect(screen.getByText("No activities yet")).toBeInTheDocument();
  });

  it("groups saved activities into morning, afternoon and evening", async () => {
    window.localStorage.setItem(
      STORAGE_KEYS.routineActivities,
      JSON.stringify([
        {
          id: "a1",
          title: "Walk",
          start: "07:00",
          durationMin: 30,
          venue: "outdoor",
          intensity: "light",
        },
        {
          id: "a2",
          title: "Commute",
          start: "14:00",
          durationMin: 45,
          venue: "outdoor",
          intensity: "moderate",
        },
        {
          id: "a3",
          title: "Indoor exercise",
          start: "19:30",
          durationMin: 60,
          venue: "indoor",
          intensity: "vigorous",
        },
      ]),
    );
    render(<RoutineView />);

    expect(await screen.findByRole("heading", { name: "Morning" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Afternoon" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Evening" })).toBeInTheDocument();
    expect(screen.getByText("to 20:30")).toBeInTheDocument();
    expect(screen.getAllByText("Vigorous").length).toBeGreaterThan(0);
  });

  it("shows field-level validation errors and does not store an invalid activity", async () => {
    const user = userEvent.setup();
    render(<RoutineView />);

    await user.click(await screen.findByRole("button", { name: /Add to routine/ }));

    expect(await screen.findByText("Give the activity a name.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.routineActivities)).toBeNull();
  });

  it("rejects a duration below fifteen minutes", async () => {
    const user = userEvent.setup();
    render(<RoutineView />);

    await user.type(await screen.findByLabelText("Activity"), "Short walk");
    const duration = screen.getByLabelText("Minutes");
    await user.clear(duration);
    await user.type(duration, "10");
    await user.click(screen.getByRole("button", { name: /Add to routine/ }));

    expect(await screen.findByText("Use at least 15 minutes.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.routineActivities)).toBeNull();
  });
});
