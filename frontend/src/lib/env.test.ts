import { afterEach, describe, expect, it, vi } from "vitest";

const ENV_KEY = "NEXT_PUBLIC_API_BASE_URL";

async function loadEnv(value?: string) {
  vi.resetModules();
  if (value === undefined) {
    delete process.env[ENV_KEY];
  } else {
    vi.stubEnv(ENV_KEY, value);
  }
  return import("./env");
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("public env schema", () => {
  it("defaults to localhost when the API URL is not configured", async () => {
    const { env } = await loadEnv();
    expect(env.NEXT_PUBLIC_API_BASE_URL).toBe("http://localhost:8000");
  });

  it("accepts an explicit localhost URL", async () => {
    const { env } = await loadEnv("http://localhost:8000");
    expect(env.NEXT_PUBLIC_API_BASE_URL).toBe("http://localhost:8000");
  });

  it("accepts loopback IP addresses used by local deployments", async () => {
    const { env } = await loadEnv("http://127.0.0.1:8000");
    expect(env.NEXT_PUBLIC_API_BASE_URL).toBe("http://127.0.0.1:8000");
  });

  it("accepts a public HTTPS API URL", async () => {
    const { env } = await loadEnv("https://api.saans-saathi.example");
    expect(env.NEXT_PUBLIC_API_BASE_URL).toBe("https://api.saans-saathi.example");
  });

  it("rejects non-HTTP protocols", async () => {
    await expect(loadEnv("ftp://localhost:8000")).rejects.toThrow(
      /Invalid frontend environment configuration/,
    );
  });

  it("rejects malformed URLs", async () => {
    await expect(loadEnv("not-a-url")).rejects.toThrow(
      /Invalid frontend environment configuration/,
    );
  });
});
