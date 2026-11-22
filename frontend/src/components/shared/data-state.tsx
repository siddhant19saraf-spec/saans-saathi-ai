"use client";

import { CloudOff, RefreshCw, TriangleAlert } from "lucide-react";
import type * as React from "react";

import type { ResourceState } from "@/features/api/resource";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/feedback";

export function DataState<T>({
  state,
  retry,
  children,
  loadingLabel = "Loading data",
  unavailableTitle = "Data service not connected",
  idle = null,
}: {
  state: ResourceState<T>;
  retry?: () => void;
  children: (data: T) => React.ReactNode;
  loadingLabel?: string;
  unavailableTitle?: string;
  idle?: React.ReactNode;
}) {
  if (state.status === "idle") {
    return <>{idle}</>;
  }

  if (state.status === "loading") {
    return (
      <div aria-busy="true" aria-live="polite" className="space-y-3">
        <span className="sr-only">{loadingLabel}</span>
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-5 w-64" />
      </div>
    );
  }

  if (state.status === "unavailable" || state.status === "error") {
    const unavailable = state.status === "unavailable";
    return (
      <Alert variant={unavailable ? "neutral" : "error"}>
        {unavailable ? (
          <CloudOff className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        ) : (
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        )}
        <AlertDescription className="flex-1">
          <AlertTitle>{unavailable ? unavailableTitle : "Something went wrong"}</AlertTitle>
          <p className="mt-1">{state.message}</p>
          {retry ? (
            <Button type="button" variant="outline" size="sm" className="mt-3" onClick={retry}>
              <RefreshCw className="size-3.5" aria-hidden="true" />
              Retry
            </Button>
          ) : null}
        </AlertDescription>
      </Alert>
    );
  }

  if (state.status === "success") {
    return <>{children(state.data)}</>;
  }

  return null;
}
