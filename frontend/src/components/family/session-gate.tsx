"use client";

import Link from "next/link";
import { Lock, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";

export function SessionGate({
  onStart,
  busy,
}: {
  onStart: (healthConsent: boolean) => Promise<string | null>;
  busy: boolean;
}) {
  const [healthConsent, setHealthConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setError(null);
    const message = await onStart(healthConsent);
    if (message) {
      setError(message);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-5 text-brand-700" aria-hidden="true" />
          Start an anonymous session
        </CardTitle>
        <p className="text-sm leading-relaxed text-ink-muted">
          Your household profile, activity preferences and recommendation history are stored in the
          SAANS SAATHI database under a random session token kept in this browser. There is no
          account, name, email or phone number. The session expires automatically, and you can
          delete everything from this page.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {error ? (
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div className="rounded-xl border border-line bg-slate-50/60 p-4">
          <div className="flex items-start gap-3">
            <Checkbox
              id="session-health-consent"
              checked={healthConsent}
              onCheckedChange={(checked) => setHealthConsent(checked === true)}
            />
            <div className="space-y-1">
              <label
                htmlFor="session-health-consent"
                className="cursor-pointer text-sm font-medium text-ink"
              >
                Also store general health flags (optional)
              </label>
              <p className="text-xs leading-relaxed text-ink-muted">
                Asthma or reactive airways, seasonal allergy, COPD or another chronic lung
                condition, a heart condition, or pregnancy. These flags add general precautions to
                activity guidance. They are not a diagnosis or a medical assessment. You can grant
                or skip this consent now and change it later by editing the profile.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="flex items-center gap-1.5 text-xs text-slate-500">
            <Lock className="size-3.5" aria-hidden="true" />
            No account, no email. The backend stores only a hash of the token.
          </p>
          <Button type="button" onClick={start} disabled={busy}>
            {busy ? "Starting session…" : "Start session"}
          </Button>
        </div>

        <p className="text-xs text-ink-muted">
          Read the{" "}
          <Link href="/settings#local-data" className="font-medium text-brand-800 hover:underline">
            data controls
          </Link>{" "}
          before continuing.
        </p>
      </CardContent>
    </Card>
  );
}
