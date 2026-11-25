import { afterEach, describe, expect, it, vi } from "vitest";

import { apiData } from "@/features/api/client";

import { postCopilotChat } from "./api";
import type { CopilotAnswer } from "./schema";

vi.mock("@/features/api/client", () => ({
  apiData: vi.fn(),
}));

const answer: CopilotAnswer = {
  conversation_id: "conv-1",
  message_id: "msg-1",
  answer: "Keep windows closed until the evening.",
  severity: "moderate",
  actions: [],
  avoid: [],
  citations: [],
  source: "deterministic",
  model: null,
  latency_ms: 12,
  disclaimer: "Guidance only, not medical advice.",
};

describe("postCopilotChat", () => {
  afterEach(() => {
    vi.mocked(apiData).mockReset();
  });

  it("posts the message to the copilot endpoint", async () => {
    vi.mocked(apiData).mockResolvedValue(answer);

    const result = await postCopilotChat({ message: "Should I open the windows?" });

    expect(result).toBe(answer);
    expect(apiData).toHaveBeenCalledTimes(1);
    const [path, schema, options] = vi.mocked(apiData).mock.calls[0]!;
    expect(path).toBe("/api/v1/copilot/chat");
    expect(schema).toBeDefined();
    expect(options).toMatchObject({
      method: "POST",
      body: { message: "Should I open the windows?" },
    });
  });

  it("forwards a conversation id when continuing a thread", async () => {
    vi.mocked(apiData).mockResolvedValue(answer);

    await postCopilotChat({ message: "And tomorrow?", conversation_id: "conv-123" });

    expect(vi.mocked(apiData).mock.calls[0]![2]).toMatchObject({
      body: { message: "And tomorrow?", conversation_id: "conv-123" },
    });
  });

  it("propagates API failures to the caller", async () => {
    vi.mocked(apiData).mockRejectedValue(new Error("copilot unavailable"));

    await expect(postCopilotChat({ message: "Hello" })).rejects.toThrow("copilot unavailable");
  });
});
