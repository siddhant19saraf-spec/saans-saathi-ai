import { Badge } from "@/components/ui/badge";
import { pollutantMeta } from "@/features/air-quality/severity";
import type { AirReading } from "@/features/air-quality/schemas";
import { formatValue } from "@/lib/format";

export function PollutantGrid({ reading }: { reading: AirReading }) {
  return (
    <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {pollutantMeta.map((pollutant) => {
        const value = reading[pollutant.key];
        return (
          <li
            key={pollutant.key}
            className="rounded-xl border border-line bg-slate-50/60 px-3 py-2.5"
          >
            <p className="flex items-center justify-between gap-2 text-[11px] font-medium text-ink-muted">
              {pollutant.label}
              <span className="text-[10px] font-normal text-slate-500">{pollutant.unit}</span>
            </p>
            <p className="mt-1 text-xl font-semibold tracking-tight text-ink">
              {value === null || value === undefined ? (
                <span className="text-slate-400">—</span>
              ) : (
                formatValue(value, 1)
              )}
            </p>
            {value === null || value === undefined ? (
              <Badge variant="outline" className="mt-1 px-1.5 py-0 text-[10px]">
                Not reported
              </Badge>
            ) : (
              <span className="sr-only">Reported by the connected provider</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
