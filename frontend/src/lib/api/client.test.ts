import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { ApiError, apiRequest } from "./client";

const payloadSchema = z.object({ status: z.string() });

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("validates and returns the parsed response body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiRequest("/api/v1/health", { schema: payloadSchema })).resolves.toEqual({
      status: "ok",
    });

    const [url, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(url.toString()).toBe("http://localhost:8000/api/v1/health");
    expect(init.method).toBe("GET");
    expect(init.cache).toBe("no-store");
  });

  it("serializes JSON bodies and sets the content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/things", {
      method: "POST",
      body: { name: "sample" },
      schema: payloadSchema,
    });

    const [, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ name: "sample" }));
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
  });

  it("maps problem+json failures onto ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            type: "about:blank",
            title: "Not Found",
            status: 404,
            detail: "Resource missing.",
            instance: "/api/v1/missing",
            code: "NOT_FOUND",
            request_id: "abc-123-def",
          },
          404,
        ),
      ),
    );

    const error = await apiRequest("/api/v1/missing", { schema: payloadSchema }).catch(
      (caught: unknown) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      code: "NOT_FOUND",
      message: "Resource missing.",
      requestId: "abc-123-def",
    });
  });

  it("falls back to a generic error for non-JSON failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("upstream error", { status: 502 })),
    );

    const error = await apiRequest("/api/v1/health", { schema: payloadSchema }).catch(
      (caught: unknown) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 502, code: "UNKNOWN_ERROR", requestId: null });
  });

  it("reports schema violations instead of returning untrusted data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ status: 200 })));

    await expect(apiRequest("/api/v1/health", { schema: payloadSchema })).rejects.toThrow();
  });

  it("wraps transport failures as NETWORK_ERROR", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(apiRequest("/api/v1/health", { schema: payloadSchema })).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
      code: "NETWORK_ERROR",
    });
  });
});
