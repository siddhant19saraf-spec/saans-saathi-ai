const steps = [
  {
    title: "Choose a location",
    description:
      "Add coordinates, select a point on the OpenStreetMap view, or use device location. Saved places stay in this browser.",
  },
  {
    title: "See the data state first",
    description:
      "Each data surface says whether it is loading, fresh, stale, partial, unavailable or failed — before any number appears.",
  },
  {
    title: "Add household context",
    description:
      "Age bands, health flags and activity levels let guidance account for who is actually breathing the air.",
  },
  {
    title: "Act with the evidence attached",
    description:
      "CPCB category, provider, observation time and freshness travel with the guidance. No number is shown without its source.",
  },
];

export function HowItWorks() {
  return (
    <section id="features" aria-labelledby="how-heading" className="border-b border-line">
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-brand-700 uppercase">
              How it works
            </p>
            <h2
              id="how-heading"
              className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl"
            >
              Designed for decisions, not dashboards
            </h2>
            <p className="mt-3 text-base leading-relaxed text-ink-muted">
              The interface is built around one rule: the meaning of a number depends on where it
              came from and how old it is.
            </p>
            <div
              className="mt-6 rounded-xl border border-brand-100 bg-brand-50/70 p-4 text-sm leading-relaxed text-brand-900"
            >
              The intelligence modules — household risk, routine planning, indoor estimates and the
              copilot — are wired to backend services that are not connected in this build. Their
              pages say so and keep local planning available. Air quality is connected through
              labelled model data and optional ground-station observations.
            </div>
          </div>

          <ol className="grid gap-4 sm:grid-cols-2">
            {steps.map((step, index) => (
              <li
                key={step.title}
                className="rounded-2xl border border-line bg-white p-5 shadow-card"
              >
                <span
                  aria-hidden="true"
                  className="inline-flex size-8 items-center justify-center rounded-lg bg-brand-700 text-xs font-semibold text-white"
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-3 text-sm font-semibold text-ink">{step.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{step.description}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}