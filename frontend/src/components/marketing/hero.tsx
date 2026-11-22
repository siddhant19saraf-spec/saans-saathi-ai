import Link from "next/link";
import { ArrowRight, ShieldCheck, Wind } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import { InterfacePreview } from "./interface-preview";

export function Hero() {
  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden border-b border-line"
    >
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_at_top,black,transparent_72%)]"
      />
      <div
        aria-hidden="true"
        className="absolute -top-24 -right-24 size-96 rounded-full bg-brand-100/60 blur-3xl"
      />

      <div className="relative mx-auto grid w-full max-w-6xl items-center gap-12 px-4 py-14 sm:px-6 sm:py-20 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>
              <Wind className="size-3.5" aria-hidden="true" />
              Urban air quality assistant
            </Badge>
            <Badge variant="outline">Hack2Skill PromptWars · Challenge 6</Badge>
          </div>

          <h1
            id="hero-heading"
            className="mt-5 text-4xl font-semibold tracking-tight text-ink sm:text-5xl lg:text-[3.4rem] lg:leading-[1.05]"
          >
            Every Breath Matters.
            <br />
            <span className="bg-gradient-to-r from-brand-800 to-accent-700 bg-clip-text text-transparent">
              Every Decision Counts.
            </span>
          </h1>

          <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-muted">
            SAANS SAATHI AI turns air-quality data into household-level decisions — with the AQI
            standard, data source and freshness stated on every screen.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild size="lg">
              <Link href="/dashboard">
                Open dashboard
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/air-quality">Explore air intelligence</Link>
            </Button>
          </div>

          <p className="mt-6 flex items-center gap-2 text-sm text-ink-muted">
            <ShieldCheck className="size-4 shrink-0 text-brand-700" aria-hidden="true" />
            CPCB 2014 AQI · no fabricated readings · provenance shown with data
          </p>
        </div>

        <InterfacePreview />
      </div>
    </section>
  );
}
