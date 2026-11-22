import type { Metadata } from "next";

export const metadata: Metadata = {
  // The root layout's title template only applies to nested segments.
  title: { absolute: "Project status · SAANS SAATHI AI" },
};

const statusItems = [
  {
    label: "Frontend shell",
    value: "Implemented",
    detail: "Next.js App Router, strict TypeScript, Tailwind, tested error and loading states.",
  },
  {
    label: "Backend foundation",
    value: "Implemented",
    detail: "FastAPI app, configuration validation, structured logging, health endpoint.",
  },
  {
    label: "Database foundation",
    value: "Implemented",
    detail: "Async SQLAlchemy engine, pooling, Alembic baseline. No business tables yet.",
  },
  {
    label: "Air quality intelligence",
    value: "Not implemented",
    detail:
      "AQI computation, forecasting, family profiles and the AI copilot are outside this release.",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-16 sm:px-6">
      <p className="text-sm font-medium tracking-wide text-brand-700 uppercase">
        Engineering foundation
      </p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
        SAANS SAATHI AI
      </h1>
      <p className="mt-5 max-w-2xl text-lg text-slate-600">
        An urban air quality assistant in early development. This build contains the verified
        engineering foundation only. It does not yet read air quality data, compute an Air Quality
        Index, or produce AI guidance.
      </p>

      <section aria-labelledby="status-heading" className="mt-12">
        <h2 id="status-heading" className="text-2xl font-semibold text-slate-900">
          What is in this release
        </h2>
        <ul className="mt-6 grid gap-4 sm:grid-cols-2">
          {statusItems.map((item) => (
            <li key={item.label} className="rounded-xl border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-medium text-slate-900">{item.label}</h3>
                <span
                  className={
                    item.value === "Implemented"
                      ? "rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700"
                      : "rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800"
                  }
                >
                  {item.value}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-600">{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
