import Link from "next/link";
import { ArrowRight, MapPin } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section aria-labelledby="cta-heading" className="bg-canvas">
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-canvas p-6 text-white shadow-raised sm:px-10 sm:py-14">
          <div aria-hidden="true" className="surface-grid absolute inset-0 opacity-20" />
          <div className="relative max-w-2xl">
            <p className="flex items-center gap-2 text-xs font-semibold tracking-[0.16em] text-brand-200 uppercase">
              <MapPin className="size-3.5" aria-hidden="true" />
              Start with your location
            </p>
            <h2 id="cta-heading" className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Build the habit of checking the air before the plan.
            </h2>
            <p className="mt-3 text-base leading-relaxed text-white/90">
              Open the dashboard, save a place, and see exactly what is connected — and what is
              still waiting for a data service.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild size="lg" className="bg-white text-brand-900 hover:bg-brand-50">
                <Link href="/dashboard">
                  Open dashboard
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="border-white/40 bg-transparent text-white hover:bg-white/10"
              >
                <Link href="/family">Set up a household profile</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}