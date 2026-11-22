import { Accessibility, Check, Eye, Keyboard, Lock, MonitorSmartphone } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const commitments = [
  {
    icon: Keyboard,
    title: "Keyboard first",
    description:
      "Every route, menu, dialog and form works without a pointer, with visible focus and logical order.",
  },
  {
    icon: Eye,
    title: "Never colour alone",
    description:
      "AQI severity always pairs colour with a text label and an icon. Charts include screen-reader tables.",
  },
  {
    icon: MonitorSmartphone,
    title: "Responsive by design",
    description:
      "Sidebar, mobile navigation and the dashboard grid are built for small screens and large ones.",
  },
  {
    icon: Lock,
    title: "Session-based privacy",
    description:
      "Routine plans, logs and checklist progress stay in this browser. The family profile is stored under an anonymous session token with explicit delete controls.",
  },
];

export function AccessibilitySection() {
  return (
    <section id="accessibility" aria-labelledby="a11y-heading" className="border-b border-line">
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">
              Accessibility &amp; privacy
            </p>
            <h2
              id="a11y-heading"
              className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
            >
              Built to WCAG 2.2 AA intent
            </h2>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-ink-muted">
              Accessibility is treated as a product requirement, not a cleanup task. Automated
              checks support the work but do not replace manual keyboard and screen-reader review.
            </p>
          </div>
          <Badge variant="default" className="w-fit">
            <Accessibility className="size-3.5" aria-hidden="true" />
            AA intent
          </Badge>
        </div>

        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {commitments.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.title} className="rounded-2xl border border-line bg-white p-5">
                <Icon className="size-5 text-brand-700" aria-hidden="true" />
                <h3 className="mt-3 flex items-center gap-2 text-sm font-semibold text-ink">
                  <Check className="size-4 text-brand-700" aria-hidden="true" />
                  {item.title}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{item.description}</p>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
