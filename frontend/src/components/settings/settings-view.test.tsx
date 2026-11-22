import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { SettingsView } from "@/components/settings/settings-view";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

function renderSettings() {
  return render(
    <LocationProvider>
      <SettingsView />
    </LocationProvider>,
  );
}

describe("SettingsView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("labels every section and every locally stored group", async () => {
    renderSettings();

    expect(await screen.findByRole("heading", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Data sources and methods" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Local data" })).toBeInTheDocument();
    expect(screen.getByText("Saved locations")).toBeInTheDocument();
    expect(screen.getByText("SmartRoutine activities")).toBeInTheDocument();
    expect(screen.getByText("Impact log")).toBeInTheDocument();
    expect(screen.getByText("IndoorShield checklist")).toBeInTheDocument();
    expect(screen.getByText("Travel preferences")).toBeInTheDocument();
    expect(screen.getByText("Notification preferences")).toBeInTheDocument();
  });

  it("persists a notification preference and allows resetting it", async () => {
    const user = userEvent.setup();
    renderSettings();

    const alerts = await screen.findByRole("switch", { name: "Air quality alerts" });
    expect(alerts).not.toBeChecked();
    await user.click(alerts);
    expect(alerts).toBeChecked();
    expect(window.localStorage.getItem(STORAGE_KEYS.notificationPreferences)).toContain(
      '"airQualityAlerts":true',
    );

    const reset = screen.getByRole("button", { name: "Reset notifications" });
    await waitFor(() => expect(reset).toBeEnabled());
    await user.click(reset);
    await user.click(screen.getByRole("button", { name: "Reset notifications: confirm" }));

    expect(window.localStorage.getItem(STORAGE_KEYS.notificationPreferences)).toBeNull();
    expect(alerts).not.toBeChecked();
  });

  it("requires confirmation before clearing a local store", async () => {
    window.localStorage.setItem(
      STORAGE_KEYS.locations,
      JSON.stringify({
        items: [{ id: "loc-1", label: "Home", lat: 28.61, lon: 77.21, source: "manual" }],
        activeId: "loc-1",
      }),
    );
    const user = userEvent.setup();
    renderSettings();

    const clear = await screen.findByRole("button", { name: "Clear saved locations" });
    expect(clear).toBeEnabled();
    await user.click(clear);

    expect(
      screen.getByRole("button", { name: "Clear saved locations: confirm" }),
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).not.toBeNull();

    await user.click(
      screen.getByRole("button", { name: "Clear saved locations: confirm" }),
    );

    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();
  });

  it("disables clearing when a store is empty", async () => {
    renderSettings();

    expect(await screen.findByRole("button", { name: "Clear saved locations" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Clear impact log" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Reset notifications" })).toBeDisabled();
  });
});
