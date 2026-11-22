import { Frown, Leaf, Meh, ShieldAlert, Smile, TriangleAlert, type LucideIcon } from "lucide-react";

export const aqiCategories = [
  "good",
  "satisfactory",
  "moderate",
  "poor",
  "very_poor",
  "severe",
] as const;

export type AqiCategory = (typeof aqiCategories)[number];

type SeverityMeta = {
  label: string;
  range: string;
  summary: string;
  icon: LucideIcon;
  badge: string;
  dot: string;
  stroke: string;
};

/**
 * CPCB 2014 categories. Colour is always paired with a label and an icon so
 * severity is never communicated by colour alone.
 */
export const severityMeta: Record<AqiCategory, SeverityMeta> = {
  good: {
    label: "Good",
    range: "0–50",
    summary: "Air quality is acceptable for most people.",
    icon: Leaf,
    badge: "border-severity-good-border bg-severity-good text-severity-good-fg",
    dot: "bg-severity-good-fg",
    stroke: "var(--color-severity-good-fg)",
  },
  satisfactory: {
    label: "Satisfactory",
    range: "51–100",
    summary: "Minor discomfort is possible for sensitive groups.",
    icon: Smile,
    badge:
      "border-severity-satisfactory-border bg-severity-satisfactory text-severity-satisfactory-fg",
    dot: "bg-severity-satisfactory-fg",
    stroke: "var(--color-severity-satisfactory-fg)",
  },
  moderate: {
    label: "Moderate",
    range: "101–200",
    summary: "Sensitive groups may feel effects; plan outdoor activity carefully.",
    icon: Meh,
    badge: "border-severity-moderate-border bg-severity-moderate text-severity-moderate-fg",
    dot: "bg-severity-moderate-fg",
    stroke: "var(--color-severity-moderate-fg)",
  },
  poor: {
    label: "Poor",
    range: "201–300",
    summary: "Breathing discomfort on prolonged exposure; limit strenuous outdoor time.",
    icon: Frown,
    badge: "border-severity-poor-border bg-severity-poor text-severity-poor-fg",
    dot: "bg-severity-poor-fg",
    stroke: "var(--color-severity-poor-fg)",
  },
  very_poor: {
    label: "Very poor",
    range: "301–400",
    summary: "Respiratory effects likely; keep outdoor activity short and light.",
    icon: TriangleAlert,
    badge: "border-severity-very-poor-border bg-severity-very-poor text-severity-very-poor-fg",
    dot: "bg-severity-very-poor-fg",
    stroke: "var(--color-severity-very-poor-fg)",
  },
  severe: {
    label: "Severe",
    range: "401–500",
    summary: "Serious risk for everyone; avoid outdoor exertion.",
    icon: ShieldAlert,
    badge: "border-severity-severe-border bg-severity-severe text-severity-severe-fg",
    dot: "bg-severity-severe-fg",
    stroke: "var(--color-severity-severe-fg)",
  },
};

export const pollutantMeta = [
  {
    key: "pm2_5",
    label: "PM2.5",
    unit: "µg/m³",
    description: "Fine particles that reach deep into the lungs.",
  },
  {
    key: "pm10",
    label: "PM10",
    unit: "µg/m³",
    description: "Coarse particles from dust, roads and construction.",
  },
  {
    key: "no2_ug_m3",
    label: "NO₂",
    unit: "µg/m³",
    description: "Traffic and combustion-related gas.",
  },
  {
    key: "so2_ug_m3",
    label: "SO₂",
    unit: "µg/m³",
    description: "Released mainly by burning sulphur-bearing fuels.",
  },
  {
    key: "co_ug_m3",
    label: "CO",
    unit: "µg/m³",
    description: "Incomplete combustion; indexed as mg/m³ for CPCB AQI.",
  },
  {
    key: "o3_ug_m3",
    label: "O₃",
    unit: "µg/m³",
    description: "Ground-level ozone formed in sunlight.",
  },
] as const;

export type PollutantKey = (typeof pollutantMeta)[number]["key"];

export const POLLUTANT_KEYS = pollutantMeta.map((pollutant) => pollutant.key);
