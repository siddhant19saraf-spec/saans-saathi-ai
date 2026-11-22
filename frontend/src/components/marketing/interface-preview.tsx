import { AqiDial } from "@/components/air-quality/aqi-dial";
import { SeverityBadge } from "@/components/air-quality/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { pollutantMeta } from "@/features/air-quality/severity";

/**
 * A static preview of the dashboard. It deliberately renders empty values and
 * an explicit preview state so the landing page never implies live data.
 */
export function InterfacePreview() {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-line bg-slate-50/70 px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-slate-300" aria-hidden="true" />
          <span className="size-2 rounded-full bg-slate-300" aria-hidden="true" />
          <span className="size-2 rounded-full bg-slate-300" aria-hidden="true" />
        </div>
        <p className="text-[11px] font-medium tracking-wide text-slate-500 uppercase">
          Interface preview · not live data
        </p>
      </div>

      <div className="grid gap-4 p-4 sm:grid-cols-[auto_1fr] sm:p-5">
        <div className="flex flex-col items-center justify-center">
          <AqiDial value={null} category={null} />
          <SeverityBadge category={null} className="mt-2" />
        </div>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="neutral">No location selected</Badge>
            <Badge variant="outline">Model-based data</Badge>
          </div>

          <dl className="mt-3 grid grid-cols-3 gap-2">
            {pollutantMeta.slice(0, 6).map((pollutant) => (
              <div
                key={pollutant.key}
                className="rounded-lg border border-line bg-slate-50/60 px-2.5 py-2"
              >
                <dt className="text-[11px] font-medium text-ink-muted">{pollutant.label}</dt>
                <dd className="mt-0.5 flex items-baseline gap-1">
                  <span className="text-lg font-semibold text-slate-400">—</span>
                  <span className="text-[10px] text-slate-400">{pollutant.unit}</span>
                </dd>
              </div>
            ))}
          </dl>

          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            <p className="text-[11px] leading-relaxed text-amber-950">
              This panel shows layout only. In the product, readings carry their provider, source
              type, observation time and freshness; model output and ground-station observations are
              labelled separately.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
