import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type * as React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LocationProvider } from "@/features/locations/location-context";
import { STORAGE_KEYS } from "@/features/store/storage";

const leaflet = vi.hoisted(() => ({
  click: null as null | ((event: { latlng: { lat: number; lng: number } }) => void),
}));

vi.mock("next/dynamic", () => ({
  default: () =>
    function MapCanvasStub(props: { onPick: (lat: number, lon: number) => void }) {
      return (
        <button type="button" onClick={() => props.onPick(28.61, 77.2)}>
          Pick point
        </button>
      );
    },
}));

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TileLayer: () => <span data-testid="tile-layer" />,
  CircleMarker: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Popup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useMap: () => ({ setView: vi.fn(), getZoom: () => 4 }),
  useMapEvents: (handlers: {
    click: (event: { latlng: { lat: number; lng: number } }) => void;
  }) => {
    leaflet.click = handlers.click;
    return {};
  },
}));

import { MapCanvas } from "@/components/map/map-canvas";
import { MapView } from "@/components/map/map-view";

const LOCATIONS = [
  { id: "loc-1", label: "Home", lat: 28.6139, lon: 77.209, source: "manual" as const },
  { id: "loc-2", label: "Work", lat: 19.076, lon: 72.8777, source: "device" as const },
];

function seed(locations = LOCATIONS, activeId = "loc-1") {
  window.localStorage.setItem(
    STORAGE_KEYS.locations,
    JSON.stringify({ items: locations, activeId }),
  );
}

function renderMap() {
  return render(
    <LocationProvider>
      <MapView />
    </LocationProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
  leaflet.click = null;
});

describe("MapView", () => {
  it("shows saved places, attribution and the honest empty state", async () => {
    seed([]);
    renderMap();

    expect(await screen.findByText("OpenStreetMap")).toBeInTheDocument();
    expect(screen.getByText(/Tiles © OpenStreetMap contributors/)).toBeInTheDocument();
    expect(screen.getByText(/No saved locations yet/)).toBeInTheDocument();
    expect(screen.getByText(/No monitoring stations are plotted/)).toBeInTheDocument();
    expect(screen.getByText(/no station layer/)).toBeInTheDocument();
  });

  it("marks one active place and activates another", async () => {
    seed();
    const user = userEvent.setup();
    renderMap();

    expect(await screen.findByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Set active" }));

    await waitFor(() =>
      expect(window.localStorage.getItem(STORAGE_KEYS.locations)).toContain('"activeId":"loc-2"'),
    );
    expect(screen.getAllByText("Active")).toHaveLength(1);
  });

  it("opens the coordinate form from the add button", async () => {
    seed();
    const user = userEvent.setup();
    renderMap();

    await user.click(await screen.findByRole("button", { name: "Add coordinates" }));

    expect(await screen.findByRole("dialog", { name: "Add a location" })).toBeInTheDocument();
  });

  it("passes a picked map point into the form as a coordinate, not a reading", async () => {
    seed();
    const user = userEvent.setup();
    renderMap();

    await user.click(await screen.findByRole("button", { name: "Pick point" }));

    const dialog = await screen.findByRole("dialog", { name: "Add a location" });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByLabelText("Latitude")).toHaveValue("28.61");
    expect(screen.getByLabelText("Longitude")).toHaveValue("77.2");
  });
});

describe("MapCanvas", () => {
  it("renders saved reviewers' markers with an active label", () => {
    render(
      <MapCanvas
        locations={LOCATIONS}
        activeId="loc-1"
        onPick={vi.fn()}
        onActivate={vi.fn()}
      />,
    );

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Work")).toBeInTheDocument();
    expect(screen.getByText("Active location")).toBeInTheDocument();
    expect(screen.getByTestId("tile-layer")).toBeInTheDocument();
  });

  it("activates an inactive marker", async () => {
    const onActivate = vi.fn();
    const user = userEvent.setup();
    render(
      <MapCanvas
        locations={LOCATIONS}
        activeId="loc-1"
        onPick={vi.fn()}
        onActivate={onActivate}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Set as active" }));
    expect(onActivate).toHaveBeenCalledWith("loc-2");
  });

  it("requires confirmation before using a clicked point", async () => {
    const onPick = vi.fn();
    const user = userEvent.setup();
    render(
      <MapCanvas locations={LOCATIONS} activeId="loc-1" onPick={onPick} onActivate={vi.fn()} />,
    );

    expect(leaflet.click).not.toBeNull();
    act(() => {
      leaflet.click?.({ latlng: { lat: 19.5, lng: 75.2 } });
    });

    expect(screen.getByText(/A point on the map is a coordinate/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Use this point" }));

    expect(onPick).toHaveBeenCalledWith(19.5, 75.2);
  });
});
