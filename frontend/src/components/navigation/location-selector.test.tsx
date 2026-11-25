import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchLocationSearch } from "@/features/air-quality/api";
import { LocationProvider } from "@/features/locations/location-context";

import { LocationSelector } from "./location-selector";

vi.mock("@/features/air-quality/api", () => ({
  fetchLocationSearch: vi.fn(),
}));

const searchResult = {
  id: "geo-1",
  name: "Pune",
  admin1: "Maharashtra",
  country: "India",
  latitude: 18.5204,
  longitude: 73.8567,
};

function searchResponse(results: (typeof searchResult)[]) {
  return {
    query: "Pune",
    results,
    attribution: ["Open-Meteo geocoding"],
  };
}

function renderSelector() {
  return render(
    <LocationProvider>
      <LocationSelector />
    </LocationProvider>,
  );
}

function seedLocations() {
  window.localStorage.setItem(
    "saans.v1.locations",
    JSON.stringify({
      items: [
        { id: "loc-1", label: "Pune, Maharashtra, India", lat: 18.5204, lon: 73.8567, source: "manual" },
        { id: "loc-2", label: "Mumbai, Maharashtra, India", lat: 19.076, lon: 72.8777, source: "manual" },
      ],
      activeId: "loc-1",
    }),
  );
}

describe("LocationSelector", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(fetchLocationSearch).mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("invites the user to add a place when nothing is saved", () => {
    renderSelector();
    expect(screen.getByText(/No saved places yet\./)).toBeInTheDocument();
    expect(screen.getByText("No active location")).toBeInTheDocument();
  });

  it("lists saved places with the active one marked", () => {
    seedLocations();
    renderSelector();

    expect(screen.getByText("Active · Pune, Maharashtra, India")).toBeInTheDocument();
    const pune = screen.getByRole("button", { name: /Pune, Maharashtra, India/ });
    const mumbai = screen.getByRole("button", { name: /Mumbai, Maharashtra, India/ });
    expect(pune).toHaveAttribute("aria-pressed", "true");
    expect(mumbai).toHaveAttribute("aria-pressed", "false");
  });

  it("switches the active place when a saved chip is pressed", async () => {
    seedLocations();
    const user = userEvent.setup();
    renderSelector();

    await user.click(screen.getByRole("button", { name: /Mumbai, Maharashtra, India/ }));

    expect(screen.getByRole("button", { name: /Mumbai, Maharashtra, India/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("Active · Mumbai, Maharashtra, India")).toBeInTheDocument();
  });

  it("searches after a pause and shows matching places", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pu" } });

    expect(fetchLocationSearch).not.toHaveBeenCalled();
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    expect(fetchLocationSearch).toHaveBeenCalledTimes(1);
    expect(vi.mocked(fetchLocationSearch).mock.calls[0]![0]).toBe("Pu");
    expect(vi.mocked(fetchLocationSearch).mock.calls[0]![2]).toEqual({ limit: 6 });

    expect(screen.getByRole("listbox", { name: "Location search results" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Pune/ })).toBeInTheDocument();
  });

  it("saves a chosen search result as the active location", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    fireEvent.click(screen.getByRole("option", { name: /Pune/ }));

    expect(screen.getByText("Active · Pune, Maharashtra, India")).toBeInTheDocument();
    expect(screen.getByText("Pune, Maharashtra, India is now the active location.")).toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("explains when no place matches the query", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([]));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Atlantis" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    expect(screen.getByText("No matching place found.")).toBeInTheDocument();
  });

  it("falls back gracefully when search fails", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockRejectedValue(new Error("network down"));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    expect(
      screen.getByText("Search is unavailable right now. Add coordinates directly instead."),
    ).toBeInTheDocument();
  });

  it("supports keyboard selection of a result", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    fireEvent.keyDown(input, { key: "ArrowDown" });
    expect(input).toHaveAttribute("aria-activedescendant", expect.stringContaining("option-0"));
    fireEvent.keyDown(input, { key: "ArrowUp" });
    expect(input).toHaveAttribute("aria-activedescendant", expect.stringContaining("option-0"));

    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByText("Active · Pune, Maharashtra, India")).toBeInTheDocument();
  });

  it("closes the results list on Escape", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("resets the search when the query is cleared", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));

    expect(input).toHaveValue("");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("reopens results on focus once a search has completed", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();

    fireEvent.focus(input);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("links to the map picker", () => {
    renderSelector();
    const link = screen.getByRole("link", { name: "Pick on map" });
    expect(link).toHaveAttribute("href", "/map");
  });

  it("ignores short queries and aborts a pending search", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "P" } });
    await act(async () => {
      vi.advanceTimersByTime(400);
    });
    expect(fetchLocationSearch).not.toHaveBeenCalled();

    fireEvent.change(input, { target: { value: "Pune" } });
    fireEvent.change(input, { target: { value: "P" } });
    await act(async () => {
      vi.advanceTimersByTime(400);
    });
    expect(fetchLocationSearch).not.toHaveBeenCalled();
  });

  it("announces result counts for assistive technology", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    const live = screen.getByText("1 places found");
    expect(live).toHaveClass("sr-only");
  });

  it("exposes the results as a labelled listbox", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockResolvedValue(searchResponse([searchResult]));
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    const list = screen.getByRole("listbox");
    const option = within(list).getByRole("option");
    expect(option).toHaveAttribute("aria-selected", "false");
  });

  it("survives a search rejection without an error message", async () => {
    vi.useFakeTimers();
    vi.mocked(fetchLocationSearch).mockRejectedValue("offline");
    renderSelector();

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    expect(
      screen.getByText("Search is unavailable right now. Add coordinates directly instead."),
    ).toBeInTheDocument();
  });

  it("does not show results for an aborted request", async () => {
    vi.useFakeTimers();
    let resolveSearch: ((value: ReturnType<typeof searchResponse>) => void) | undefined;
    vi.mocked(fetchLocationSearch)
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveSearch = resolve;
          }),
      )
      .mockResolvedValueOnce(searchResponse([]));
    renderSelector();

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByText("Searching…")).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "Mumbai" } });
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByText("No matching place found.")).toBeInTheDocument();

    await act(async () => {
      resolveSearch?.(searchResponse([searchResult]));
      await Promise.resolve();
    });

    expect(screen.queryByRole("option", { name: /Pune/ })).not.toBeInTheDocument();
    expect(screen.getByText("No matching place found.")).toBeInTheDocument();
  });
});
