"use client";

import { useCallback, useEffect, useState } from "react";
import { CreditCard, Loader2, Lock, Sparkles } from "lucide-react";
import ChatThread from "@/components/ChatThread";
import { fetchCards } from "@/lib/banking";
import { label, maskNumber } from "@/lib/format";
import { useAgentChat } from "@/lib/useAgentChat";
import type { Card } from "@/lib/types";

export default function CardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshCards = useCallback(() => {
    return fetchCards()
      .then(data => {
        if (data) {
          setCards(data);
          setError("");
        } else {
          setError("Could not load your cards.");
        }
      })
      .catch(() => setError("Could not load your cards."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refreshCards();
  }, [refreshCards]);

  // Blocking goes through the assistant, so it gets the same confirmation
  // step as a chat request (no direct API call from this page).
  const chat = useAgentChat({ onActivity: refreshCards });

  const requestBlock = (card: Card) => {
    chat.send(`Block my card ending ${card.card_last4}`);
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden p-6 gap-6">
      <div className="w-full lg:w-1/2 flex flex-col gap-4 overflow-y-auto pr-2 pb-6">
        <div>
          <h1 className="text-2xl font-semibold text-white">Cards</h1>
          <p className="text-sm text-gray-400 mt-1">Your cards and their status. Blocking a card always asks you to confirm.</p>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {loading ? (
          <div className="h-32 glass-panel rounded-2xl animate-pulse flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
          </div>
        ) : cards.length === 0 && !error ? (
          <p className="text-sm text-gray-500">No cards found</p>
        ) : (
          <ul className="grid gap-4">
            {cards.map(card => {
              const active = card.status === "active";
              return (
                <li key={card.id} className="glass-panel p-5 rounded-2xl flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400"><CreditCard className="w-5 h-5" /></div>
                    <div>
                      <p className="text-white font-medium">{label(card.card_type)} card</p>
                      <p className="text-sm font-mono text-gray-400">{maskNumber(card.card_last4)}</p>
                      {card.expiry_month && card.expiry_year && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Expires {String(card.expiry_month).padStart(2, "0")}/{String(card.expiry_year).slice(-2)}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full border ${
                      active ? "border-green-500/30 text-green-400 bg-green-500/10" : "border-red-500/30 text-red-400 bg-red-500/10"
                    }`}>
                      {label(card.status)}
                    </span>
                    {active && (
                      <button
                        type="button"
                        onClick={() => requestBlock(card)}
                        disabled={chat.isTyping || chat.pending !== null}
                        className="text-xs px-3 py-1.5 rounded-lg border border-red-500/40 text-red-300 hover:bg-red-500/10 disabled:opacity-40 flex items-center gap-1"
                      >
                        <Lock className="w-3 h-3" /> Block card
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="w-full lg:w-1/2 flex flex-col bg-surface/50 rounded-3xl border border-surface-border overflow-hidden">
        <div className="h-14 border-b border-surface-border flex items-center gap-2 px-6 bg-surface">
          <Sparkles className="w-4 h-4 text-primary-400" />
          <h2 className="text-sm font-semibold text-white">Assistant</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {chat.messages.length === 0 ? (
            <p className="text-sm text-gray-500">Choose &quot;Block card&quot; to ask the assistant to block a card. You will be asked to confirm.</p>
          ) : (
            <ChatThread
              messages={chat.messages}
              isTyping={chat.isTyping}
              pending={chat.pending}
              onConfirm={chat.confirm}
              onCancel={chat.cancel}
            />
          )}
        </div>
      </div>
    </div>
  );
}
