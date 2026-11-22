import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-20 text-center sm:px-6">
      <p className="text-sm font-medium tracking-wide text-brand-700 uppercase">404</p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">Page not found</h1>
      <p className="mt-4 text-slate-600">The page you requested does not exist in this release.</p>
      <Link
        href="/"
        className="mt-8 inline-block rounded-lg bg-brand-700 px-5 py-2.5 font-medium text-white hover:bg-brand-600"
      >
        Back to home
      </Link>
    </div>
  );
}
