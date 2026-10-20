"use client";

import { useCallback, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { apiFetch } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolName?: string | null;
  data?: unknown;
}

// POST /api/v1/chat response (errors carry `detail` instead).
interface ChatResponse {
  message?: string;
  tool_name?: string | null;
  data?: unknown;
  requires_confirmation?: boolean;
  confirmation_challenge?: string | null;
  action_summary?: string | null;
  detail?: unknown;
}

export interface PendingConfirmation {
  challengeCode: string;
  summary: string;
}

/**
 * One conversation with the agent, including the confirmation flow:
 * HIGH/CRITICAL actions come back as a pending confirmation; confirm() sends
 * the challenge code, cancel() discards it on the server too.
 */
export function useAgentChat(options: { greeting?: string; onActivity?: () => void } = {}) {
  const { greeting, onActivity } = options;
  const conversationId = useRef(uuidv4());
  const [messages, setMessages] = useState<ChatMessage[]>(
    greeting ? [{ id: "msg-0", role: "assistant", content: greeting }] : [],
  );
  const [isTyping, setIsTyping] = useState(false);
  const [pending, setPending] = useState<PendingConfirmation | null>(null);

  const say = useCallback((content: string) => {
    setMessages(prev => [...prev, { id: uuidv4(), role: "assistant", content }]);
  }, []);

  const send = useCallback(async (userMessage: string, challengeCode?: string) => {
    setMessages(prev => [...prev, { id: uuidv4(), role: "user", content: userMessage }]);
    setIsTyping(true);
    try {
      const res = await apiFetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId.current,
          ...(challengeCode ? { challenge_code: challengeCode } : {}),
        }),
      });
      const data: ChatResponse = await res.json();

      if (!res.ok) {
        say(typeof data.detail === "string" ? data.detail : "The request could not be completed.");
        return;
      }

      setMessages(prev => [...prev, {
        id: uuidv4(),
        role: "assistant",
        content: data.message || "Done.",
        toolName: data.tool_name,
        data: data.data,
      }]);
      if (data.requires_confirmation && data.confirmation_challenge) {
        setPending({ challengeCode: data.confirmation_challenge, summary: data.action_summary || "Confirm this action" });
      }
      onActivity?.();
    } catch {
      say("I'm having trouble connecting to the banking core right now.");
    } finally {
      setIsTyping(false);
    }
  }, [onActivity, say]);

  const confirm = useCallback(async () => {
    if (!pending) return;
    const { challengeCode } = pending;
    setPending(null);
    await send("Confirm", challengeCode);
  }, [pending, send]);

  const cancel = useCallback(() => {
    setPending(null);
    // Discard the server-side pending action too (it would expire in 5 min).
    apiFetch(`/api/v1/chat/conversations/${conversationId.current}/pending-action`, { method: "DELETE" })
      .catch(e => console.error(e));
    say("Cancelled. No action was taken.");
  }, [say]);

  return { messages, isTyping, pending, send, confirm, cancel };
}
