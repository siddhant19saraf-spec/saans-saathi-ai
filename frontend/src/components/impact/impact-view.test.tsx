import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ImpactView } from "@/components/impact/impact-view";
import { STORAGE_KEYS } from "@/features/store/storage";

const FACTORS = [
  {
    key: "car.petrol.small",
    label: "Petrol car (small)",
    value: 0.192,
    unit: "kgCO2e/km",
    source: "DEFRA 2023",
    source_url: "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023",
    version: "2023",
    retrieved_at: "2026-11-18",
  },
];

function stubFactors() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ data: FACTORS, meta: {} }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    ),
  );
}

describe("ImpactView", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows factor provenance from the server and never computes a total locally", async () => {
    stubFactors();
    render(<ImpactView />);

    expect(await screen.findByText("Petrol car (small)")).toBeInTheDocument();
    expect(screen.getByText(/DEFRA 2023/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Source" })).toHaveAttribute(
      "href",
      FACTORS[0]!.source_url,
    );
    expect(screen.getByText(/No CO₂e figure is computed in the browser/)).toBeInTheDocument();
  });

  it("adds an entry, shows the entered quantity and removes it", async () => {
    stubFactors();
    const user = userEvent.setup();
    render(<ImpactView />);

    await user.type(screen.getByLabelText("Quantity"), "5");
    await user.click(screen.getByRole("button", { name: /Add/ }));

    const log = screen.getByRole("list");
    expect(within(log).getByText("Walked or cycled instead of driving")).toBeInTheDocument();
    expect(within(log).getByText(/5 km/)).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.impactActivities)).toContain('"quantity":5');

    await user.click(screen.getByRole("button", { name: /Remove .* entry/ }));

    expect(screen.getByText("Nothing logged yet")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.impactActivities)).toBe("[]");
  });

  it("rejects a non-positive quantity without storing anything", async () => {
    stubFactors();
    const user = userEvent.setup();
    render(<ImpactView />);

    await user.type(screen.getByLabelText("Quantity"), "0");
    await user.click(screen.getByRole("button", { name: /Add/ }));

    expect(await screen.findByText("Enter a quantity greater than zero.")).toBeInTheDocument();
    expect(window.localStorage.getItem(STORAGE_KEYS.impactActivities)).toBeNull();
  });

  it("labels an unavailable factor registry instead of inventing factors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    render(<ImpactView />);

    expect(await screen.findByText("Factor registry not connected")).toBeInTheDocument();
    expect(screen.getByText(/The API could not be reached/)).toBeInTheDocument();
  });
});
