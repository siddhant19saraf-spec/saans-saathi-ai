import { Clock3, FlaskConical, Users } from "lucide-react";

const problems = [
  {
    icon: Clock3,
    title: "Place and hour matter",
    description:
      "Air quality changes through the day and across a city. A daily city-wide number rarely reflects the air outside a specific home at a specific hour.",
  },
  {
    icon: Users,
    title: "Households differ",
    description:
      "Children, older adults, pregnant people and people with respiratory conditions need different precautions from the same reading.",
  },
  {
    icon: FlaskConical,
    title: "Claims need evidence",
    description:
      "Carbon savings, exposure and indoor estimates are only useful when their assumptions, data and limits are visible.",
  },
];

export function ProblemSection() {
  return (
    <section id="about" aria-labelledby="about-heading" className="border-b border-line">
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">
          Why SAANS SAATHI
        </p>
        <h2
          id="about-heading"
          className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
        >
          Air-quality advice is usually generic. Breathing isn&apos;t.
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-ink-muted">
          SAANS SAATHI AI is designed as a decision workspace, not another index display. It keeps
          the evidence attached to the advice.
        </p>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {problems.map((problem) => {
            const Icon = problem.icon;
            return (
              <article
                key={problem.title}
                className="rounded-2xl border border-line bg-white p-6 shadow-card"
              >
                <span className="inline-flex size-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                  <Icon className="size-5" aria-hidden="true" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-ink">{problem.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">{problem.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
