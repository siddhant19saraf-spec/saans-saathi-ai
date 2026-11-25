import Link from "next/link";
import { ArrowRight, Bot, ShieldCheck, Sparkles, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const exampleQuestions = [
  "Which two hours today look best for a walk with my child?",
  "What does a CPCB AQI of 180 mean for my household?",
  "Should I ventilate the kitchen while cooking today?",
];

const boundaries = [
  "No answer without a grounded data context.",
  "No Gemini key in browser code — server-side only.",
  "No simulated replies when the AI service is unavailable.",
];

export function CopilotSection() {
  return (
    <section aria-labelledby="copilot-heading" className="border-b border-line bg-white">
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="grid items-start gap-10 lg:grid-cols-2">
          <div>
            <p className="flex items-center gap-2 text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">
              <Sparkles className="size-3.5" aria-hidden="true" />
              SAANS AI Copilot
            </p>
            <h2
              id="copilot-heading"
              className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
            >
              Grounded questions, not a guessing game
            </h2>
            <p className="mt-3 text-base leading-relaxed text-ink-muted">
              The copilot is designed to explain the numbers already computed by the platform —
              category, dominant pollutant, timing and household context. It is an explainer, not a
              source of measurements.
            </p>

            <ul className="mt-6 flex flex-col gap-2">
              {exampleQuestions.map((question) => (
                <li
                  key={question}
                  className="rounded-xl border border-line bg-slate-50 px-4 py-3 text-sm text-ink-muted"
                >
                  “{question}”
                </li>
              ))}
            </ul>

            <Button asChild className="mt-6">
              <Link href="/copilot">
                Open copilot
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </div>

          <div className="rounded-2xl border border-line bg-canvas p-5 shadow-card sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <p className="flex items-center gap-2 text-sm font-semibold text-ink">
                <Bot className="size-4 text-brand-700" aria-hidden="true" />
                Copilot status
              </p>
              <Badge variant="warning">Not connected</Badge>
            </div>

            <div className="mt-4 rounded-xl border border-line bg-white p-4">
              <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                In this build
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
                The copilot page accepts a question and calls the backend endpoint. Because the AI
                and session services are not connected, it reports an unavailable state — it never
                fabricates an answer.
              </p>
            </div>

            <ul className="mt-4 flex flex-col gap-2">
              {boundaries.map((boundary) => (
                <li key={boundary} className="flex items-start gap-2 text-sm text-ink-muted">
                  <X className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
                  {boundary}
                </li>
              ))}
            </ul>

            <p
              className="mt-4 flex items-start gap-2 rounded-xl border border-brand-100 bg-brand-50 p-3 text-xs leading-relaxed text-brand-900"
            >
              <ShieldCheck className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              Numeric fields are computed by deterministic backend services and re-validated before
              display. Prose never becomes the source of a reading.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}