import Link from "next/link";
import { ArrowRight, CalendarClock, House, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";

const actions = [
  {
    href: "/smart-routine",
    title: "SmartRoutine",
    description:
      "Plan the day around the hours you care about. Timing guidance activates when the air-quality service is connected.",
    icon: CalendarClock,
  },
  {
    href: "/indoor-shield",
    title: "IndoorShield",
    description:
      "Work through ventilation, dust, kitchen and filtration actions with general, source-labelled guidance.",
    icon: House,
  },
  {
    href: "/copilot",
    title: "SAANS AI Copilot",
    description:
      "Ask grounded questions about the displayed data. The copilot never answers without a data context.",
    icon: Sparkles,
  },
];

export function SmartActions() {
  return (
    <section aria-labelledby="actions-heading" className="space-y-4">
      <div>
        <h2 id="actions-heading" className="text-lg font-semibold text-ink">
          Smart actions
        </h2>
        <p className="mt-0.5 text-sm text-ink-muted">Move from the reading to a decision.</p>
      </div>
      <ul className="grid gap-4 md:grid-cols-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <li key={action.href}>
              <Card className="h-full transition-shadow hover:shadow-raised">
                <Link
                  href={action.href}
                  className="flex h-full flex-col gap-3 p-5 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none"
                >
                  <span className="inline-flex size-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                    <Icon className="size-5" aria-hidden="true" />
                  </span>
                  <span className="text-base font-semibold text-ink">{action.title}</span>
                  <span className="text-sm leading-relaxed text-ink-muted">
                    {action.description}
                  </span>
                  <span className="mt-auto inline-flex items-center gap-1 text-xs font-semibold text-brand-700">
                    Open {action.title}
                    <ArrowRight className="size-3.5" aria-hidden="true" />
                  </span>
                </Link>
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
