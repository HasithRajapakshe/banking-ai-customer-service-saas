"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import ConfirmCard from "@/components/ConfirmCard";
import ToolResultView from "@/components/ToolResultView";
import type { ChatMessage, PendingConfirmation } from "@/lib/useAgentChat";

type Props = {
  messages: ChatMessage[];
  isTyping: boolean;
  pending: PendingConfirmation | null;
  onConfirm: () => void;
  onCancel: () => void;
};

// Assistant text, plus a compact view of list results (never raw JSON).
export default function ChatThread({ messages, isTyping, pending, onConfirm, onCancel }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping, pending]);

  return (
    <div className="space-y-6">
      {messages.map(msg => (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          key={msg.id}
          data-role={msg.role}
          className={`flex gap-4 max-w-[85%] ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
        >
          <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
            msg.role === "user" ? "bg-surface-hover border border-surface-border" : "bg-primary-500/20 text-primary-400"
          }`}>
            {msg.role === "user" ? <User className="w-4 h-4 text-gray-400" /> : <Bot className="w-4 h-4" />}
          </div>

          <div className={`space-y-2 min-w-0 ${msg.role === "user" ? "items-end" : "items-start"}`}>
            <div className={`px-5 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
              msg.role === "user"
                ? "bg-white text-black rounded-tr-sm"
                : "bg-surface border border-surface-border text-gray-200 rounded-tl-sm"
            }`}>
              {msg.content}
            </div>
            {msg.role === "assistant" && <ToolResultView toolName={msg.toolName} data={msg.data} />}
          </div>
        </motion.div>
      ))}

      {isTyping && (
        <div className="flex gap-4 max-w-[85%]" data-typing>
          <div className="w-8 h-8 rounded-full bg-primary-500/20 text-primary-400 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div className="px-5 py-4 rounded-2xl bg-surface border border-surface-border rounded-tl-sm flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
        </div>
      )}

      {pending && !isTyping && (
        <div className="max-w-[85%] ml-12">
          <ConfirmCard summary={pending.summary} onConfirm={onConfirm} onCancel={onCancel} />
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
