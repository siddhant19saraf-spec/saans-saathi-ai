import Link from "next/link";
import { ArrowUpRight, Leaf, Users, Wind, CalendarClock } from "lucide-react";

import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";

const ACTIONS = [
  {
    href: "/air-quality",
    title: "Air intelligence",
    description: "Pollutants, source and forecast",
    icon: Wind,
  },
  {
    href: "/family",
    title: "Family intelligence",
    description: "Household profile and consent",
    icon: Users,
  },
  {
    href: "/smart-routine",
    title: "SmartRoutine",
    description: "Plan around lower-exposure hours",
    icon: CalendarClock,
  },
  {
    href: "/impact",
    title: "Impact log",
    description: "Record low-carbon actions",
    icon: Leaf,
  },
] as const;

export function QuickActions() {
  return (
    <section aria-labelledby="quick-actions-heading" className="space-y-3">
      <SectionHeader
        id="quick-actions-heading"
        title="Quick actions"
        description="Jump straight into the workspace you need."
      />
      <ul className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <li key={action.href}>
              <Card className="card-lift h-full hover:border-brand-200 hover:shadow-raised">
                <Link
                  href={action.href}
                  className="flex h-full flex-col gap-2 p-3.5 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none sm:p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="inline-flex size-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                      <Icon className="size-4.5" aria-hidden="true" />
                    </span>
                    <ArrowUpRight
                      className="size-3.5 text-ink-subtle transition-transform group-hover:translate-x-0.5"
                      aria-hidden="true"
                    />
                  </div>
                  <span className="text-sm font-semibold text-ink">{action.title}</span>
                  <span className="text-xs leading-relaxed text-ink-muted">
                    {action.description}
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
