import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CopilotView } from "@/components/copilot/copilot-view";
import type { CopilotAnswer } from "@/features/copilot/schema";
import { ApiError } from "@/lib/api/client";

const mocks = vi.hoisted(() => ({ postCopilotChat: vi.fn() }));

vi.mock("@/features/copilot/api", () => ({
  postCopilotChat: mocks.postCopilotChat,
}));

const ANSWER: CopilotAnswer = {
  conversation_id: "conv-1",
  message_id: "msg-1",
  answer: "Outdoor PM2.5 peaks near 19:00. Walk between 06:30 and 07:00.",
  severity: "moderate",
  actions: [
    {
      title: "Walk at 06:30",
      detail: "Forecast PM2.5 is lowest then.",
      time_window: "06:30-07:00",
      fact_refs: ["aq.forecast.min_pm2_5"],
      confidence: "high",
    },
  ],
  avoid: [{ title: "Outdoor exercise after 18:00", reason_fact_ref: "aq.forecast.max_pm2_5" }],
  citations: [
    {
      fact_id: "aq.forecast.min_pm2_5",
      label: "Lowest forecast PM2.5",
      value: 48.2,
      unit: "µg/m³",
      source: "Open-Meteo (CAMS)",
      observed_at: "2026-11-19T06:00:00Z",
    },
  ],
  source: "ai",
  model: "gemini-3.5-flash-lite",
  latency_ms: 1840,
  disclaimer: "General guidance, not medical advice.",
};

async function ask(question: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Ask the Copilot"), question);
  await user.click(screen.getByRole("button", { name: /send/i }));
  return user;
}

describe("CopilotView", () => {
  afterEach(() => {
    mocks.postCopilotChat.mockReset();
  });

  it("does not send an empty question", async () => {
    const user = userEvent.setup();
    render(<CopilotView />);

    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText("Write a question first.")).toBeInTheDocument();
    expect(mocks.postCopilotChat).not.toHaveBeenCalled();
  });

  it("reports an unavailable service and never fabricates an answer", async () => {
    mocks.postCopilotChat.mockRejectedValue(
      new ApiError({ message: "Not found", status: 404, code: "NOT_FOUND" }),
    );
    render(<CopilotView />);

    await ask("When should I walk?");

    expect(await screen.findByText("Copilot service not connected")).toBeInTheDocument();
    expect(screen.getByText(/No answer was generated/)).toBeInTheDocument();
    expect(screen.queryByText(/Outdoor PM2.5 peaks/)).not.toBeInTheDocument();
  });

  it("renders only the response the service returned, with citations", async () => {
    mocks.postCopilotChat.mockResolvedValue(ANSWER);
    render(<CopilotView />);

    await ask("When should I walk?");

    expect(await screen.findByText(/Outdoor PM2\.5 peaks near 19:00/)).toBeInTheDocument();
    expect(screen.getByText("Walk at 06:30")).toBeInTheDocument();
    expect(screen.getByText("Lowest forecast PM2.5")).toBeInTheDocument();
    expect(screen.getByText(/48\.2 µg\/m³/)).toBeInTheDocument();
    expect(screen.getByText(/General guidance, not medical advice/)).toBeInTheDocument();
    expect(screen.getByText(/AI-generated, grounded/)).toBeInTheDocument();
    expect(mocks.postCopilotChat).toHaveBeenCalledWith({
      message: "When should I walk?",
    });
  });

  it("reuses the conversation id on the next turn", async () => {
    mocks.postCopilotChat.mockResolvedValue(ANSWER);
    const user = userEvent.setup();
    render(<CopilotView />);

    await user.type(screen.getByLabelText("Ask the Copilot"), "First question");
    await user.click(screen.getByRole("button", { name: /send/i }));
    expect(await screen.findByText(/Outdoor PM2\.5 peaks/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: /send/i })).toBeEnabled());

    await user.type(screen.getByLabelText("Ask the Copilot"), "Second question");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() =>
      expect(mocks.postCopilotChat).toHaveBeenLastCalledWith({
        message: "Second question",
        conversation_id: "conv-1",
      }),
    );
  });
});
