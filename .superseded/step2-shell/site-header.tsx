import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Link href="/" className="text-base font-semibold tracking-tight text-slate-900">
          SAANS SAATHI AI
        </Link>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          Foundation build
        </span>
      </div>
    </header>
  );
}
