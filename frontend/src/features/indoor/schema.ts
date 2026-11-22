import { z } from "zod";

export const INDOOR_CATEGORIES = [
  { value: "ventilation", label: "Ventilation" },
  { value: "dust", label: "Dust" },
  { value: "kitchen", label: "Kitchen" },
  { value: "filtration", label: "Filtration" },
] as const;

export type IndoorCategory = (typeof INDOOR_CATEGORIES)[number]["value"];

export const INDOOR_CHECKLIST = [
  {
    id: "windows-closed-peak",
    category: "ventilation",
    title: "Keep windows closed during peak outdoor pollution",
    guidance:
      "Ventilate when outdoor PM2.5 is lowest, typically early morning in many Indian cities. This is general guidance, not a reading from a sensor in your home.",
  },
  {
    id: "cross-ventilation",
    category: "ventilation",
    title: "Use short cross-ventilation bursts",
    guidance:
      "Opening windows on opposite sides for a few minutes exchanges air faster than leaving one window ajar all day.",
  },
  {
    id: "door-mats",
    category: "dust",
    title: "Place mats at entrances and remove shoes indoors",
    guidance:
      "Most indoor dust is tracked in from outside. Mats and a no-shoes rule reduce resuspension.",
  },
  {
    id: "damp-wipe",
    category: "dust",
    title: "Damp-wipe surfaces instead of dry dusting",
    guidance: "Dry dusting lifts fine particles back into the air; a damp cloth captures them.",
  },
  {
    id: "cooking-ventilation",
    category: "kitchen",
    title: "Run the exhaust fan or open a window while cooking",
    guidance:
      "Cooking, especially frying, is a major indoor particle source. Ventilate during and for several minutes after cooking.",
  },
  {
    id: "biomass-warning",
    category: "kitchen",
    title: "Avoid burning biomass indoors",
    guidance:
      "Firewood, dung and crop residue produce very high indoor particle concentrations. Prefer cleaner fuels and outdoor cooking where possible.",
  },
  {
    id: "filter-maintenance",
    category: "filtration",
    title: "Clean or replace purifier filters on schedule",
    guidance:
      "A loaded filter reduces airflow and cleaning effectiveness. Follow the device manufacturer's interval.",
  },
  {
    id: "purifier-sizing",
    category: "filtration",
    title: "Match purifier CADR to room size",
    guidance:
      "As a rule of thumb, choose a clean-air delivery rate of at least five times the room volume per hour.",
  },
] as const;

export type IndoorChecklistItem = (typeof INDOOR_CHECKLIST)[number];

export const indoorChecklistSchema = z.record(z.string(), z.boolean());

export type IndoorChecklist = z.infer<typeof indoorChecklistSchema>;
