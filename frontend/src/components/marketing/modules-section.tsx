import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { allNavItems, settingsItem } from "@/components/navigation/nav-config";

const statusByHref: Record<
  string,
  { label: string; variant: "default" | "neutral" | "outline" | "warning" }
> = {
  "/dashboard": { label: "Workspace", variant: "default" },
  "/air-quality": { label: "Needs data service", variant: "warning" },
  "/map": { label: "OpenStreetMap", variant: "outline" },
  "/family": { label: "Local profile", variant: "default" },
  "/smart-routine": { label: "Local planner", variant: "default" },
  "/indoor-shield": { label: "Guidance checklist", variant: "default" },
  "/eco-route": { label: "Needs routing service", variant: "warning" },
  "/impact": { label: "Local log", variant: "default" },
  "/copilot": { label: "Needs AI service", variant: "warning" },
};

export function ModulesSection() {
  const modules = allNavItems.filter((item) => item.href !== settingsItem.href);

  return (
    <section
      id="modules"
      aria-labelledby="modules-heading"
      className="border-b border-line bg-white"
    >
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">Modules</p>
        <h2
          id="modules-heading"
          className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
        >
          One workspace, nine connected surfaces
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-ink-muted">
          Every module is reachable from the sidebar and each states whether it works locally or is
          waiting for a connected service.
        </p>

        <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((item) => {
            const Icon = item.icon;
            const status = statusByHref[item.href] ?? {
              label: "Workspace",
              variant: "outline" as const,
            };
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="group flex h-full flex-col rounded-2xl border border-line bg-surface p-5 shadow-card transition-shadow hover:shadow-raised focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 focus-visible:outline-none"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="inline-flex size-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                      <Icon className="size-5" aria-hidden="true" />
                    </span>
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </div>
                  <h3 className="mt-4 flex items-center gap-1.5 text-base font-semibold text-ink">
                    {item.label}
                    <ArrowUpRight
                      className="size-4 text-slate-400 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
                      aria-hidden="true"
                    />
                  </h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
                    {item.description}
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
