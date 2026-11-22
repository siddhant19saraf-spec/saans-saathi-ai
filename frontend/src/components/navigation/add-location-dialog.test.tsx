import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AddLocationButton } from "@/components/navigation/add-location-dialog";
import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

function renderWithLocations() {
  return render(
    <LocationProvider>
      <AddLocationButton />
    </LocationProvider>,
  );
}

describe("AddLocationDialog", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows field-level errors and does not save invalid coordinates", async () => {
    const user = userEvent.setup();
    renderWithLocations();

    await user.click(screen.getByRole("button", { name: "Add location" }));
    await user.click(await screen.findByRole("button", { name: "Save location" }));

    expect(await screen.findByText("Enter a name for this location.")).toBeInTheDocument();
    expect(screen.getByText("Enter a latitude.")).toBeInTheDocument();
    expect(screen.getByText("Enter a longitude.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();
  });

  it("rejects an out-of-range latitude", async () => {
    const user = userEvent.setup();
    renderWithLocations();

    await user.click(screen.getByRole("button", { name: "Add location" }));

    await user.type(await screen.findByLabelText("Location name"), "Home");
    await user.type(screen.getByLabelText("Latitude"), "200");
    await user.type(screen.getByLabelText("Longitude"), "72.87");
    await user.click(screen.getByRole("button", { name: "Save location" }));

    expect(await screen.findByText("Latitude must be between -90 and 90.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();
  });

  it("saves a valid location to this browser and closes", async () => {
    const user = userEvent.setup();
    renderWithLocations();

    await user.click(screen.getByRole("button", { name: "Add location" }));

    await user.type(await screen.findByLabelText("Location name"), "Home");
    await user.type(screen.getByLabelText("Latitude"), "19.076");
    await user.type(screen.getByLabelText("Longitude"), "72.877");
    await user.click(screen.getByRole("button", { name: "Save location" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    const raw = window.localStorage.getItem(STORAGE_KEYS.locations);
    expect(raw).not.toBeNull();
    const stored = JSON.parse(raw ?? "{}") as {
      items: { label: string; lat: number }[];
    };
    expect(stored.items).toHaveLength(1);
    expect(stored.items[0]?.label).toBe("Home");
    expect(stored.items[0]?.lat).toBeCloseTo(19.076);
  });

  it("offers city results without choosing one silently", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            data: {
              query: "Pune",
              results: [
                {
                  id: "1269321",
                  name: "Pune",
                  latitude: 18.5204,
                  longitude: 73.8567,
                  country: "India",
                  country_code: "IN",
                  admin1: "Maharashtra",
                  timezone: "Asia/Kolkata",
                  population: 3124458,
                },
                {
                  id: "1269322",
                  name: "Pune City",
                  latitude: 18.5196,
                  longitude: 73.8554,
                  country: "India",
                  country_code: "IN",
                  admin1: "Maharashtra",
                  timezone: "Asia/Kolkata",
                  population: 1000000,
                },
              ],
              attribution: ["Open-Meteo Geocoding API", "GeoNames"],
            },
            meta: {},
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      ),
    );

    renderWithLocations();
    await user.click(screen.getByRole("button", { name: "Add location" }));

    await user.type(await screen.findByLabelText("Search for a city or place"), "Pune");
    await user.click(screen.getByRole("button", { name: "Search" }));

    const first = await screen.findByRole("button", { name: /Pune, Maharashtra, India/ });
    const second = screen.getByRole("button", { name: /Pune City, Maharashtra, India/ });
    expect(first).toBeInTheDocument();
    expect(second).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();

    await user.click(first);

    expect(screen.getByLabelText("Location name")).toHaveValue("Pune");
    expect(screen.getByLabelText("Latitude")).toHaveValue("18.5204");
    expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toBeNull();
  });
});
