import Link from "next/link";
import { Wind } from "lucide-react";

const columns = [
  {
    title: "Workspace",
    links: [
      { href: "/dashboard", label: "Dashboard" },
      { href: "/air-quality", label: "Air intelligence" },
      { href: "/map", label: "Pollution map" },
    ],
  },
  {
    title: "Protection",
    links: [
      { href: "/family", label: "Family intelligence" },
      { href: "/smart-routine", label: "SmartRoutine" },
      { href: "/indoor-shield", label: "IndoorShield" },
    ],
  },
  {
    title: "Sustainability",
    links: [
      { href: "/eco-route", label: "EcoRoute" },
      { href: "/impact", label: "Impact intelligence" },
      { href: "/copilot", label: "SAANS AI Copilot" },
    ],
  },
  {
    title: "Trust",
    links: [
      { href: "/settings#data-sources", label: "Data sources" },
      { href: "/#accessibility", label: "Accessibility" },
      { href: "/#about", label: "About this build" },
    ],
  },
];

export function MarketingFooter() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_2.6fr]">
          <div>
            <p className="flex items-center gap-2 text-sm font-semibold text-ink">
              <span className="inline-flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-brand-700 to-accent-700 text-white">
                <Wind className="size-4" aria-hidden="true" />
              </span>
              SAANS SAATHI AI
            </p>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-ink-muted">
              Environmental intelligence for everyday breathing. Every Breath Matters. Every
              Decision Counts.
            </p>
            <p className="mt-4 max-w-sm text-xs leading-relaxed text-slate-500">
              Engineering build. Air quality uses labelled model data, with ground-station
              observations kept separate. Household intelligence and the AI copilot remain local
              until their services are connected.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            {columns.map((column) => (
              <div key={column.title}>
                <p className="text-xs font-semibold tracking-[0.12em] text-slate-500 uppercase">
                  {column.title}
                </p>
                <ul className="mt-3 flex flex-col gap-2">
                  {column.links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="rounded text-sm text-ink-muted underline-offset-4 transition-colors hover:text-brand-800 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-line pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} SAANS SAATHI AI · v0.1.0 engineering build</p>
          <p>CPCB 2014 AQI standard · map tiles © OpenStreetMap contributors</p>
        </div>
      </div>
    </footer>
  );
}
