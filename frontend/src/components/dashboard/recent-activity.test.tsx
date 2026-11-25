import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { RecentActivity } from "./recent-activity";

const ROUTINE_KEY = "saans.v1.routine.activities";
const IMPACT_KEY = "saans.v1.impact.activities";

function seedRoutine() {
  window.localStorage.setItem(
    ROUTINE_KEY,
    JSON.stringify([
      { id: "r-2", title: "Evening walk", start: "18:30", durationMin: 30, venue: "outdoor", intensity: "light" },
      { id: "r-1", title: "Morning run", start: "06:15", durationMin: 45, venue: "outdoor", intensity: "vigorous" },
      { id: "r-3", title: "Indoor stretch", start: "12:00", durationMin: 15, venue: "indoor", intensity: "light" },
      { id: "r-4", title: "Fourth activity", start: "20:00", durationMin: 20, venue: "indoor", intensity: "moderate" },
    ]),
  );
}

function seedImpact() {
  window.localStorage.setItem(
    IMPACT_KEY,
    JSON.stringify([
      { id: "i-1", type: "walked", quantity: 4.5, occurredOn: "2026-11-20" },
      { id: "i-2", type: "public-transport", quantity: 12, occurredOn: "2026-11-21" },
      { id: "i-3", type: "planted-tree", quantity: 2, occurredOn: "2026-11-22" },
      { id: "i-4", type: "worked-from-home", quantity: 1, occurredOn: "2026-11-23" },
    ]),
  );
}

describe("RecentActivity", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("invites the user to start when no activity is stored", async () => {
    render(<RecentActivity />);

    expect(await screen.findByText("No activity yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Plan a routine" })).toHaveAttribute(
      "href",
      "/smart-routine",
    );
    expect(screen.getByRole("link", { name: "Log an action" })).toHaveAttribute("href", "/impact");
  });

  it("shows the three earliest routine entries sorted by start time", async () => {
    seedRoutine();
    render(<RecentActivity />);

    const routineCard = (await screen.findByText("Today's routine")).closest("div")!.parentElement!;
    expect(within(routineCard).getByText("Morning run")).toBeInTheDocument();
    expect(within(routineCard).getByText("Indoor stretch")).toBeInTheDocument();
    expect(within(routineCard).getByText("Evening walk")).toBeInTheDocument();
    expect(within(routineCard).queryByText("Fourth activity")).not.toBeInTheDocument();
  });

  it("shows routine metadata with venue, intensity and duration", async () => {
    seedRoutine();
    render(<RecentActivity />);

    expect(
      await screen.findByText("Outdoors · Vigorous · 45 min"),
    ).toBeInTheDocument();
    expect(screen.getByText("Indoors · Light · 15 min")).toBeInTheDocument();
  });

  it("shows only the three most recent impact entries", async () => {
    seedImpact();
    render(<RecentActivity />);

    expect(await screen.findByText("Latest impact entries")).toBeInTheDocument();
    expect(screen.getAllByText(/Walked or cycled/).length).toBe(1);
    expect(screen.getAllByText(/Used public transport/).length).toBe(1);
    expect(screen.getAllByText(/Planted a tree/).length).toBe(1);
    expect(screen.queryByText(/Worked from home/)).not.toBeInTheDocument();
  });

  it("formats impact quantity with its unit", async () => {
    seedImpact();
    render(<RecentActivity />);

    expect(await screen.findByText("4.5 km")).toBeInTheDocument();
    expect(screen.getByText("12 km")).toBeInTheDocument();
    expect(screen.getByText("2 trees")).toBeInTheDocument();
  });

  it("explains an empty routine column when only impact entries exist", async () => {
    seedImpact();
    render(<RecentActivity />);

    expect(await screen.findByText("No routine activities saved yet.")).toBeInTheDocument();
  });

  it("explains an empty impact column when only routine entries exist", async () => {
    seedRoutine();
    render(<RecentActivity />);

    expect(await screen.findByText("Nothing logged yet.")).toBeInTheDocument();
  });

  it("links both cards to their full workspaces", async () => {
    seedRoutine();
    seedImpact();
    render(<RecentActivity />);

    const openLinks = await screen.findAllByRole("link", { name: "Open" });
    expect(openLinks).toHaveLength(2);
    expect(openLinks[0]).toHaveAttribute("href", "/smart-routine");
    expect(openLinks[1]).toHaveAttribute("href", "/impact");
    expect(screen.getByRole("link", { name: /View impact log/ })).toHaveAttribute(
      "href",
      "/impact",
    );
  });

  it("renders a labelled region with a privacy statement", async () => {
    render(<RecentActivity />);

    const region = screen.getByRole("region", { name: "Recent activity" });
    expect(
      within(region).getByText("Your latest plan and log entries. Nothing is sent anywhere."),
    ).toBeInTheDocument();
    await screen.findByText("No activity yet");
  });
});
