import { describe, expect, it } from "vitest";

import { aqiCategories, pollutantMeta, severityMeta } from "./severity";

describe("CPCB severity metadata", () => {
  it("exposes the six CPCB 2014 categories in order", () => {
    expect(aqiCategories).toEqual([
      "good",
      "satisfactory",
      "moderate",
      "poor",
      "very_poor",
      "severe",
    ]);
  });

  it("gives every category a text label, a range and an icon", () => {
    for (const category of aqiCategories) {
      const meta = severityMeta[category];
      expect(meta.label.length).toBeGreaterThan(0);
      expect(meta.range).toMatch(/^\d+–\d+$/);
      expect(meta.icon).toBeDefined();
    }
  });

  it("documents each pollutant with a unit and description", () => {
    expect(pollutantMeta.map((pollutant) => pollutant.key)).toEqual([
      "pm2_5",
      "pm10",
      "no2_ug_m3",
      "so2_ug_m3",
      "co_ug_m3",
      "o3_ug_m3",
    ]);
    for (const pollutant of pollutantMeta) {
      expect(pollutant.unit.length).toBeGreaterThan(0);
      expect(pollutant.description.length).toBeGreaterThan(0);
    }
  });
});
