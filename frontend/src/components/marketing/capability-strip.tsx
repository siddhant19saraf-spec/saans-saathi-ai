import { Accessibility, Database, MapPin, ScanSearch } from "lucide-react";

const items = [
  {
    icon: ScanSearch,
    title: "CPCB 2014 AQI",
    description:
      "The national AQI is computed and labelled as CPCB. Other provider scales are kept separate.",
  },
  {
    icon: Database,
    title: "Source-aware states",
    description:
      "Loading, unavailable, stale and error states are first-class — never replaced with sample values.",
  },
  {
    icon: MapPin,
    title: "Location you control",
    description:
      "Choose coordinates on a map or use device location. Up to eight places stay on your device.",
  },
  {
    icon: Accessibility,
    title: "Accessible by default",
    description:
      "Semantic landmarks, keyboard paths, visible focus and text alternatives for every chart.",
  },
];

export function CapabilityStrip() {
  return (
    <section aria-label="Product principles" className="border-b border-line bg-white">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-10 sm:grid-cols-2 sm:px-6 lg:grid-cols-4 lg:px-8">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="flex gap-3">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                <Icon className="size-4.5" aria-hidden="true" />
              </span>
              <div>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-ink-muted">{item.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
