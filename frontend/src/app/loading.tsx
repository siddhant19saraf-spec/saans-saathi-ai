export default function Loading() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="mx-auto w-full max-w-4xl px-4 py-16 sm:px-6"
    >
      <span className="sr-only">Loading content</span>
      <div aria-hidden="true" className="animate-pulse space-y-4">
        <div className="h-4 w-40 rounded bg-slate-200" />
        <div className="h-12 w-72 max-w-full rounded bg-slate-200" />
        <div className="h-4 w-full max-w-2xl rounded bg-slate-200" />
        <div className="h-4 w-full max-w-xl rounded bg-slate-200" />
      </div>
    </div>
  );
}
