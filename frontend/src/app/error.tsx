"use client";

import { useEffect } from "react";

export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // The digest is the only identifier shared with server logs; the message
    // may contain internal details, so it stays in the browser console.
    console.error("Unhandled route error", error.digest ?? "no-digest");
  }, [error]);

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-20 text-center sm:px-6">
      <h1 className="text-3xl font-semibold text-slate-900">Something went wrong</h1>
      <p className="mt-4 text-slate-600">
        This page failed to render. Try again, and if the problem continues, report it with the
        reference code below.
      </p>
      {error.digest ? (
        <p className="mt-4 font-mono text-sm text-slate-500">Reference: {error.digest}</p>
      ) : null}
      <button
        type="button"
        onClick={reset}
        className="mt-8 rounded-lg bg-brand-700 px-5 py-2.5 font-medium text-white hover:bg-brand-600"
      >
        Try again
      </button>
    </div>
  );
}
