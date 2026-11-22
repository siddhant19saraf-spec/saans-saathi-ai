import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

import { classifyApiFailure, useApiResource } from "./resource";

describe("classifyApiFailure", () => {
  it("treats an unreachable API as unavailable, not an application error", () => {
    const failure = classifyApiFailure(
      new ApiError({ message: "offline", status: 0, code: "NETWORK_ERROR" }),
    );
    expect(failure.status).toBe("unavailable");
    expect(failure.message).toMatch(/could not be reached/i);
  });

  it("treats 404, 401, 403 and 503 as unavailable services", () => {
    for (const status of [404, 401, 403, 503]) {
      const failure = classifyApiFailure(new ApiError({ message: "nope", status, code: "X" }));
      expect(failure.status).toBe("unavailable");
    }
  });

  it("keeps other HTTP errors as real errors", () => {
    const failure = classifyApiFailure(
      new ApiError({ message: "Validation failed", status: 422, code: "MESSAGE_INVALID" }),
    );
    expect(failure).toEqual({
      status: "error",
      message: "Validation failed",
      code: "MESSAGE_INVALID",
    });
  });

  it("handles unknown thrown values without leaking internals", () => {
    expect(classifyApiFailure(new Error("boom"))).toEqual({
      status: "error",
      message: "The response could not be processed.",
      code: "UNEXPECTED_ERROR",
    });
  });
});

describe("useApiResource", () => {
  it("starts idle when there is no loader", () => {
    const { result } = renderHook(() => useApiResource(null));
    expect(result.current.state.status).toBe("idle");
  });

  it("resolves a successful loader", async () => {
    const loader = vi.fn().mockResolvedValue({ value: 1 });
    const { result } = renderHook(() => useApiResource(loader));

    expect(result.current.state.status).toBe("loading");
    await waitFor(() =>
      expect(result.current.state).toEqual({ status: "success", data: { value: 1 } }),
    );
  });

  it("reports a missing service as unavailable", async () => {
    const loader = vi
      .fn()
      .mockRejectedValue(new ApiError({ message: "Not found", status: 404, code: "NOT_FOUND" }));
    const { result } = renderHook(() => useApiResource(loader));

    await waitFor(() => expect(result.current.state.status).toBe("unavailable"));
  });

  it("retries a failed request and can recover", async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(
        new ApiError({ message: "Down", status: 503, code: "SERVICE_UNAVAILABLE" }),
      )
      .mockResolvedValueOnce({ value: 2 });

    const { result } = renderHook(() => useApiResource(loader));
    await waitFor(() => expect(result.current.state.status).toBe("unavailable"));

    act(() => result.current.retry());
    expect(result.current.state.status).toBe("loading");

    await waitFor(() =>
      expect(result.current.state).toEqual({ status: "success", data: { value: 2 } }),
    );
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
