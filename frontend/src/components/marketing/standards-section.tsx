import { Info, Layers } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { aqiCategories, severityMeta } from "@/features/air-quality/severity";

export function StandardsSection() {
  return (
    <section
      id="standards"
      aria-labelledby="standards-heading"
      className="border-b border-line bg-white"
    >
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">
              Standards & evidence
            </p>
            <h2
              id="standards-heading"
              className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
            >
              One index. No mixed scales.
            </h2>
            <p className="mt-3 text-base leading-relaxed text-ink-muted">
              SAANS SAATHI surfaces the CPCB 2014 National AQI for India. If a data provider also
              returns a US or European AQI, those values are shown separately and labelled with
              their own standard.
            </p>

            <div className="mt-6 flex flex-col gap-3">
              <div className="flex gap-3 rounded-xl border border-line bg-slate-50 p-4">
                <Layers className="mt-0.5 size-4 shrink-0 text-brand-700" aria-hidden="true" />
                <p className="text-sm leading-relaxed text-ink-muted">
                  A US AQI of 80 is not the same condition as a CPCB AQI of 80. The interface never
                  maps one onto the other.
                </p>
              </div>
              <div className="flex gap-3 rounded-xl border border-line bg-slate-50 p-4">
                <Info className="mt-0.5 size-4 shrink-0 text-brand-700" aria-hidden="true" />
                <p className="text-sm leading-relaxed text-ink-muted">
                  Monitoring stations are never invented. Ground-station data is shown only when a
                  provider returns it, and model output is labelled as model-based forecast data.
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-line">
            <table className="w-full border-collapse text-left text-sm">
              <caption className="sr-only">CPCB 2014 AQI categories, ranges and meanings</caption>
              <thead>
                <tr className="bg-slate-50">
                  <th
                    scope="col"
                    className="px-4 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase"
                  >
                    Category
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase"
                  >
                    AQI range
                  </th>
                  <th
                    scope="col"
                    className="hidden px-4 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase sm:table-cell"
                  >
                    Meaning
                  </th>
                </tr>
              </thead>
              <tbody>
                {aqiCategories.map((category) => {
                  const meta = severityMeta[category];
                  const Icon = meta.icon;
                  return (
                    <tr key={category} className="border-t border-line">
                      <th scope="row" className="px-4 py-3 font-medium">
                        <Badge className={meta.badge}>
                          <Icon className="size-3.5" aria-hidden="true" />
                          {meta.label}
                        </Badge>
                      </th>
                      <td className="px-4 py-3 text-ink-muted">{meta.range}</td>
                      <td className="hidden px-4 py-3 text-xs leading-relaxed text-ink-muted sm:table-cell">
                        {meta.summary}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="border-t border-line bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
              Categories follow the CPCB National Air Quality Index methodology. The computed index
              is always accompanied by the pollutants used and a partial-coverage flag.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}