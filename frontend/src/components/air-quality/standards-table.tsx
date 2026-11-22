import { Badge } from "@/components/ui/badge";
import { aqiCategories, severityMeta } from "@/features/air-quality/severity";

export function StandardsTable() {
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-white">
      <div className="border-b border-line px-5 py-4">
        <h2 className="text-base font-semibold text-ink">CPCB 2014 AQI categories</h2>
        <p className="mt-1 text-sm text-ink-muted">
          Category names and breakpoints belong to the CPCB National Air Quality Index. They are not
          interchangeable with US EPA or European categories.
        </p>
      </div>
      <table className="w-full border-collapse text-left text-sm">
        <caption className="sr-only">CPCB 2014 AQI categories, ranges and health context</caption>
        <thead>
          <tr className="bg-slate-50">
            <th
              scope="col"
              className="px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >
              Category
            </th>
            <th
              scope="col"
              className="px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase"
            >
              AQI range
            </th>
            <th
              scope="col"
              className="hidden px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase sm:table-cell"
            >
              Context
            </th>
          </tr>
        </thead>
        <tbody>
          {aqiCategories.map((category) => {
            const meta = severityMeta[category];
            const Icon = meta.icon;
            return (
              <tr key={category} className="border-t border-line">
                <th scope="row" className="px-5 py-3 font-medium">
                  <Badge className={meta.badge}>
                    <Icon className="size-3.5" aria-hidden="true" />
                    {meta.label}
                  </Badge>
                </th>
                <td className="px-5 py-3 text-ink-muted">{meta.range}</td>
                <td className="hidden px-5 py-3 text-xs leading-relaxed text-ink-muted sm:table-cell">
                  {meta.summary}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
