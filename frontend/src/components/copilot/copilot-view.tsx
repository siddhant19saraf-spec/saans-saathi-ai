"use client";

import Link from "next/link";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch } from "react-hook-form";
import { BookOpen, CloudOff, Info, Send, ShieldAlert, Sparkles, Trash2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Textarea } from "@/components/ui/field";
import { Separator, Skeleton } from "@/components/ui/feedback";
import { StatusBadge } from "@/components/ui/status-badge";
import { classifyApiFailure, type ApiFailure } from "@/features/api/resource";
import { postCopilotChat } from "@/features/copilot/api";
import {
  copilotMessageSchema,
  type CopilotAnswer,
  type CopilotMessageValues,
} from "@/features/copilot/schema";
import { formatDateTime, formatValue, titleCase } from "@/lib/format";

const SUGGESTED_PROMPTS = [
  "When is air quality best for a morning walk?",
  "What should we do indoors when pollution peaks?",
  "How can I protect a child with asthma today?",
];

type Turn =
  | { id: string; question: string; status: "loading" }
  | { id: string; question: string; status: "success"; answer: CopilotAnswer }
  | { id: string; question: string; status: "unavailable" | "error"; failure: ApiFailure };

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function CopilotView() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<CopilotMessageValues>({
    resolver: zodResolver(copilotMessageSchema),
    defaultValues: { message: "" },
  });

  const draft = useWatch({ control, name: "message" }) ?? "";

  async function send(rawMessage: string) {
    const message = rawMessage.trim();
    if (!message || pending) {
      return;
    }

    const id = newId();
    setPending(true);
    setTurns((current) => [...current, { id, question: message, status: "loading" }]);

    try {
      const answer = await postCopilotChat(
        conversationId ? { message, conversation_id: conversationId } : { message },
      );
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { id, question: message, status: "success", answer } : turn,
        ),
      );
      setConversationId(answer.conversation_id);
      reset({ message: "" });
    } catch (error) {
      const failure = classifyApiFailure(error);
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { id, question: message, status: failure.status, failure } : turn,
        ),
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,20rem)]">
      <Card className="flex min-h-[32rem] flex-col">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="size-4 text-brand-700" aria-hidden="true" />
              Grounded conversation
            </CardTitle>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={turns.length === 0 || pending}
              onClick={() => {
                setTurns([]);
                setConversationId(null);
              }}
            >
              <Trash2 className="size-3.5" aria-hidden="true" />
              Clear conversation
            </Button>
          </div>
          <p className="text-sm text-ink-muted">
            Answers are produced by the Copilot service from its own fact pack. If the service is
            not connected, no answer is generated here.
          </p>
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <StatusBadge tone="info">AI answers are labelled</StatusBadge>
            <StatusBadge tone="neutral">Fallback answers say so</StatusBadge>
          </div>
        </CardHeader>

        <CardContent className="flex flex-1 flex-col gap-4">
          <div
            role="log"
            aria-live="polite"
            aria-label="Copilot conversation"
            className="flex-1 space-y-4"
          >
            {turns.length === 0 ? (
              <div className="rounded-xl border border-dashed border-line px-4 py-6">
                <p className="text-sm font-medium text-ink">No messages yet</p>
                <p className="mt-1 text-sm text-ink-muted">
                  Ask about timing, indoor steps or protecting a household member. Every answer must
                  cite the facts it used.
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => setValue("message", prompt, { shouldValidate: true })}
                      className="rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:border-brand-300 hover:text-brand-800 focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <ol className="space-y-4">
                {turns.map((turn) => (
                  <TurnItem key={turn.id} turn={turn} />
                ))}
              </ol>
            )}
          </div>

          <form
            noValidate
            onSubmit={handleSubmit((values) => {
              void send(values.message);
            })}
            className="space-y-2"
          >
            <label htmlFor="copilot-message" className="sr-only">
              Ask the Copilot
            </label>
            <Textarea
              id="copilot-message"
              placeholder="Ask about today's air, timing or indoor steps…"
              maxLength={800}
              disabled={pending}
              aria-invalid={errors.message ? true : undefined}
              aria-describedby={errors.message ? "copilot-message-error" : "copilot-message-hint"}
              className="min-h-20"
              {...register("message")}
            />
            <FieldError id="copilot-message-error">{errors.message?.message}</FieldError>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p id="copilot-message-hint" className="text-xs text-slate-500">
                {draft.trim().length}/800 characters · up to 4 links
              </p>
              <Button type="submit" disabled={pending}>
                <Send className="size-4" aria-hidden="true" />
                {pending ? "Waiting for the service" : "Send"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <BookOpen className="size-4 text-brand-700" aria-hidden="true" />
              How answers are grounded
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5 text-sm leading-relaxed text-ink-muted">
            <p>
              The service builds a fact pack from current readings and forecast data, then asks the
              model for a structured answer.
            </p>
            <p>
              Numeric claims must reference a fact that ships with its source and observation time.
              Those citations are rendered below each answer.
            </p>
            <p>
              The model API key is held by the server only. Nothing on this page calls the model
              directly.
            </p>
            <p className="rounded-lg border border-line bg-surface-muted px-2.5 py-2 text-xs">
              <span className="font-semibold text-ink">Two answer modes.</span> When the model is
              available, the answer is labelled AI-generated. When it is not, the deterministic
              rules engine composes the answer and the card says so — it is never presented as a
              Gemini response. If the Copilot service itself is unreachable, no answer is invented.
            </p>
          </CardContent>
        </Card>

        <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-4">
          <p className="flex items-center gap-2 text-sm font-semibold text-brand-900">
            <ShieldAlert className="size-4" aria-hidden="true" />
            General guidance only
          </p>
          <p className="mt-1.5 text-xs leading-relaxed text-brand-900/80">
            Copilot answers are not medical advice. Household health details are only sent when the
            account service and Copilot are both configured; this build does not attach a profile.
          </p>
          <Link
            href="/settings#data-sources"
            className="mt-2 inline-block text-xs font-semibold text-brand-800 underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:outline-none"
          >
            Review data sources
          </Link>
        </div>
      </div>
    </div>
  );
}

function TurnItem({ turn }: { turn: Turn }) {
  return (
    <li className="space-y-2">
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-brand-700 px-3.5 py-2 text-sm text-white">
          {turn.question}
        </p>
      </div>

      {turn.status === "loading" ? (
        <div aria-busy="true" className="space-y-2">
          <span className="sr-only">Waiting for the Copilot service</span>
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : null}

      {turn.status === "unavailable" || turn.status === "error" ? (
        <Alert variant={turn.status === "unavailable" ? "neutral" : "error"}>
          <CloudOff className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <AlertDescription>
            <AlertTitle>
              {turn.status === "unavailable"
                ? "Copilot service not connected"
                : "The Copilot request failed"}
            </AlertTitle>
            <p className="mt-1">{turn.failure.message}</p>
            <p className="mt-1 text-xs">
              No answer was generated. Check the dashboard for current air data, or review the data
              sources in settings.
            </p>
          </AlertDescription>
        </Alert>
      ) : null}

      {turn.status === "success" ? <AnswerCard answer={turn.answer} /> : null}
    </li>
  );
}

function severityVariant(severity: string | null) {
  switch (severity) {
    case "poor":
    case "very_poor":
      return "danger" as const;
    case "moderate":
      return "warning" as const;
    case "good":
      return "default" as const;
    default:
      return "neutral" as const;
  }
}

function AnswerCard({ answer }: { answer: CopilotAnswer }) {
  return (
    <div className="rounded-2xl rounded-bl-sm border border-line bg-white px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={severityVariant(answer.severity)}>
          {answer.severity ? titleCase(answer.severity) : "Context"}
        </Badge>
        {answer.source === "ai" ? (
          <StatusBadge tone="info">AI-generated, grounded</StatusBadge>
        ) : answer.source === "fallback" ? (
          <StatusBadge tone="warning">Deterministic fallback</StatusBadge>
        ) : (
          <StatusBadge tone="neutral">Deterministic rules answer</StatusBadge>
        )}
        <span className="text-[11px] text-ink-subtle">
          {answer.model ? `${answer.model} · ` : ""}
          {answer.latency_ms !== null ? `${formatValue(answer.latency_ms)} ms` : ""}
        </span>
      </div>

      {answer.source !== "ai" ? (
        <p className="mt-2 rounded-lg border border-line bg-surface-muted px-2.5 py-1.5 text-[11px] leading-relaxed text-ink-muted">
          {answer.source === "fallback"
            ? "The language model was unavailable, so this answer was composed by the deterministic rules engine from the cited facts. It is not a Gemini response."
            : "This answer was composed by the deterministic rules engine from the cited facts. It is not a language model response."}
        </p>
      ) : null}

      <p className="mt-2 text-sm leading-relaxed whitespace-pre-line text-ink">{answer.answer}</p>

      {answer.actions.length > 0 ? (
        <section aria-labelledby="copilot-actions" className="mt-3">
          <h4
            id="copilot-actions"
            className="text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase"
          >
            Recommended actions
          </h4>
          <ul className="mt-1.5 space-y-2">
            {answer.actions.map((action, index) => (
              <li
                key={`${action.title}-${index}`}
                className="rounded-lg border border-line bg-slate-50 px-3 py-2"
              >
                <p className="text-sm font-medium text-ink">{action.title}</p>
                <p className="mt-0.5 text-xs text-ink-muted">{action.detail}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                  {action.time_window ? <span>{action.time_window}</span> : null}
                  {action.confidence ? (
                    <span>{titleCase(action.confidence)} confidence</span>
                  ) : null}
                  {action.fact_refs.map((ref) => (
                    <code
                      key={ref}
                      className="rounded bg-white px-1 py-0.5 text-[10px] text-slate-600"
                    >
                      {ref}
                    </code>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {answer.avoid.length > 0 ? (
        <section aria-labelledby="copilot-avoid" className="mt-3">
          <h4
            id="copilot-avoid"
            className="text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase"
          >
            Consider avoiding
          </h4>
          <ul className="mt-1.5 space-y-1">
            {answer.avoid.map((item, index) => (
              <li key={`${item.title}-${index}`} className="text-xs text-ink-muted">
                <span className="font-medium text-ink">{item.title}</span>
                {item.reason_fact_ref ? (
                  <code className="ml-1.5 rounded bg-slate-100 px-1 py-0.5 text-[10px]">
                    {item.reason_fact_ref}
                  </code>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {answer.citations.length > 0 ? (
        <section aria-labelledby="copilot-citations" className="mt-3">
          <h4
            id="copilot-citations"
            className="text-[11px] font-semibold tracking-[0.12em] text-slate-500 uppercase"
          >
            Citations
          </h4>
          <ul className="mt-1.5 space-y-1.5">
            {answer.citations.map((citation) => {
              const displayValue =
                typeof citation.value === "number"
                  ? `${formatValue(citation.value, 2)}${citation.unit ? ` ${citation.unit}` : ""}`
                  : citation.value;
              return (
                <li key={citation.fact_id} className="text-xs text-ink-muted">
                  <span className="font-medium text-ink">{citation.label}</span>
                  {displayValue !== null ? <span> — {displayValue}</span> : null}
                  <span className="block text-[11px] text-slate-500">
                    {citation.source} · {formatDateTime(citation.observed_at)} ·{" "}
                    <code>{citation.fact_id}</code>
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      <Separator className="mt-3" />
      <p className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-500">
        <Info className="size-3 shrink-0" aria-hidden="true" />
        {answer.disclaimer}
      </p>
    </div>
  );
}
