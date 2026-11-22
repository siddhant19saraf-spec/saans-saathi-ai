import { apiData } from "@/features/api/client";

import { copilotAnswerSchema, type CopilotAnswer } from "./schema";

export function postCopilotChat(body: {
  message: string;
  conversation_id?: string;
}): Promise<CopilotAnswer> {
  return apiData("/api/v1/copilot/chat", copilotAnswerSchema, {
    method: "POST",
    body,
  });
}
