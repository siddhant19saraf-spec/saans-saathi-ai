import { severityMeta, type AqiCategory } from "@/features/air-quality/severity";
import { cn } from "@/lib/utils";

const RADIUS = 54;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function AqiDial({
  value,
  category,
  partial = false,
  className,
}: {
  value: number | null;
  category: AqiCategory | null;
  partial?: boolean;
  className?: string;
}) {
  const meta = category ? severityMeta[category] : null;
  const progress = value === null ? 0 : Math.min(500, Math.max(0, value)) / 500;
  const offset = CIRCUMFERENCE * (1 - progress);
  const label =
    value === null
      ? "CPCB AQI is unavailable"
      : `CPCB AQI ${Math.round(value)}, ${meta?.label ?? "unknown"} category`;

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative size-40">
        <svg viewBox="0 0 140 140" role="img" aria-label={label} className="size-full">
          <circle
            cx="70"
            cy="70"
            r={RADIUS}
            fill="none"
            stroke="var(--color-line)"
            strokeWidth="12"
          />
          {value !== null && meta ? (
            <circle
              cx="70"
              cy="70"
              r={RADIUS}
              fill="none"
              stroke={meta.stroke}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={offset}
              transform="rotate(-90 70 70)"
            />
          ) : null}
        </svg>
        <div
          aria-hidden="true"
          className="absolute inset-0 flex flex-col items-center justify-center"
        >
          <span className="text-4xl font-semibold tracking-tight text-ink">
            {value === null ? "—" : Math.round(value)}
          </span>
          <span className="mt-1 text-xs font-medium text-ink-muted">
            {meta ? meta.label : "No reading"}
          </span>
        </div>
      </div>
      <p className="mt-3 text-center text-xs leading-relaxed text-ink-muted">
        CPCB 2014 National AQI, computed from current hourly values.
        {partial ? " Some pollutants are not reported." : ""}
      </p>
    </div>
  );
}
