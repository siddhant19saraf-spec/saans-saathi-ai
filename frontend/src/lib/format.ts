const dateTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  dateStyle: "medium",
  timeStyle: "short",
});

const hourFormatter = new Intl.DateTimeFormat("en-IN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const dayFormatter = new Intl.DateTimeFormat("en-IN", {
  month: "short",
  day: "numeric",
});

export function formatDateTime(iso: string | null): string {
  if (!iso) {
    return "Not reported";
  }
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : dateTimeFormatter.format(date);
}

export function formatHour(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : hourFormatter.format(date);
}

export function formatDay(iso: string): string {
  const date = new Date(`${iso}T00:00:00`);
  return Number.isNaN(date.getTime()) ? iso : dayFormatter.format(date);
}

export function formatValue(value: number | null | undefined, maximumFractionDigits = 0): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits }).format(value);
}

export function titleCase(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
