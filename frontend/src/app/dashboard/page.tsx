"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Send, CreditCard, Wallet, Sparkles, Loader2, Receipt, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import ChatThread from "@/components/ChatThread";
import { fetchAccounts, fetchCards } from "@/lib/banking";
import { label, maskNumber, money } from "@/lib/format";
import { useAgentChat } from "@/lib/useAgentChat";
import type { Account, Card } from "@/lib/types";

export default function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [cards, setCards] = useState<Card[]>([]);
  const [loadingCards, setLoadingCards] = useState(true);
  const [input, setInput] = useState("");

  const refreshAccounts = useCallback(() => {
    return fetchAccounts()
      .then(data => {
        if (data) setAccounts(data);
      })
      .catch(e => console.error(e))
      .finally(() => setLoadingAccounts(false));
  }, []);

  const refreshCards = useCallback(() => {
    return fetchCards()
      .then(data => {
        if (data) setCards(data);
      })
      .catch(e => console.error(e))
      .finally(() => setLoadingCards(false));
  }, []);

  useEffect(() => {
    refreshAccounts();
    refreshCards();
  }, [refreshAccounts, refreshCards]);

  // Refresh after every reply in case the agent changed something (e.g. blocked a card).
  const onActivity = useCallback(() => {
    refreshAccounts();
    refreshCards();
  }, [refreshAccounts, refreshCards]);

  const chat = useAgentChat({
    greeting: "Hello! I'm your Nexus AI Assistant. How can I help you manage your finances today?",
    onActivity,
  });

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = input.trim();
    setInput("");
    await chat.send(userMessage);
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden p-6 gap-6">

      {/* Left Column: Accounts & cards */}
      <div className="w-full lg:w-1/3 flex flex-col gap-6 overflow-y-auto pr-2 pb-6">
        <div>
          <h2 className="text-2xl font-semibold text-white mb-6">Financial Overview</h2>

          <div className="grid gap-4">
            {loadingAccounts ? (
              <div className="h-32 glass-panel rounded-2xl animate-pulse flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
              </div>
            ) : accounts.length === 0 ? (
              <div className="h-32 glass-panel rounded-2xl flex flex-col items-center justify-center text-gray-400">
                <Wallet className="w-8 h-8 mb-2 opacity-50" />
                <p>No accounts found</p>
              </div>
            ) : (
              accounts.map((acc, i) => (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  key={acc.id}
                  className="glass-panel p-6 rounded-2xl relative overflow-hidden group"
                >
                  <div className="absolute -right-10 -top-10 w-32 h-32 bg-primary-500/10 rounded-full blur-2xl group-hover:bg-primary-500/20 transition-all" />

                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <p className="text-sm text-gray-400 mb-1">{label(acc.account_type).toUpperCase()}</p>
                      <p className="text-xs font-mono text-gray-500">{maskNumber(acc.account_number)}</p>
                    </div>
                    <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                      <Wallet className="w-4 h-4 text-primary-400" />
                    </div>
                  </div>

                  <p className="text-3xl font-bold text-white tracking-tight">
                    {money(acc.current_balance, acc.currency)}
                  </p>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* My cards (summary; full list on the Cards page) */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">My cards</h2>
            <Link href="/dashboard/cards" className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1">
              Manage <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          {loadingCards ? (
            <div className="h-20 glass-panel rounded-2xl animate-pulse flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
            </div>
          ) : cards.length === 0 ? (
            <p className="text-sm text-gray-500">No cards found</p>
          ) : (
            <ul className="grid gap-3">
              {cards.map(card => (
                <li key={card.id} className="glass-panel px-4 py-3 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400"><CreditCard className="w-4 h-4" /></div>
                    <div>
                      <p className="text-sm text-white">{label(card.card_type)} card</p>
                      <p className="text-xs font-mono text-gray-500">{maskNumber(card.card_last4)}</p>
                    </div>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full border ${
                      card.status === "active"
                        ? "border-green-500/30 text-green-400 bg-green-500/10"
                        : "border-red-500/30 text-red-400 bg-red-500/10"
                    }`}
                  >
                    {label(card.status)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Shortcuts (only to features that exist) */}
        <div className="grid grid-cols-2 gap-4">
          <Link href="/dashboard/cards" className="glass-panel p-4 rounded-xl flex items-center gap-3 hover:bg-white/5 transition-colors">
            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400"><CreditCard className="w-4 h-4" /></div>
            <div>
              <p className="text-sm font-medium text-white">Cards</p>
              <p className="text-xs text-gray-500">Status &amp; block</p>
            </div>
          </Link>
          <Link href="/dashboard/transactions" className="glass-panel p-4 rounded-xl flex items-center gap-3 hover:bg-white/5 transition-colors">
            <div className="p-2 bg-green-500/10 rounded-lg text-green-400"><Receipt className="w-4 h-4" /></div>
            <div>
              <p className="text-sm font-medium text-white">Transactions</p>
              <p className="text-xs text-gray-500">Recent activity</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Right Column: AI Chat */}
      <div className="w-full lg:w-2/3 h-full flex flex-col bg-surface/50 rounded-3xl border border-surface-border overflow-hidden relative shadow-2xl">
        <div className="h-16 border-b border-surface-border flex items-center px-6 bg-surface z-10 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 p-0.5">
              <div className="w-full h-full bg-black rounded-full flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Nexus Assistant</h2>
              <p className="text-xs text-green-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 block" /> Online
              </p>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <ChatThread
            messages={chat.messages}
            isTyping={chat.isTyping}
            pending={chat.pending}
            onConfirm={chat.confirm}
            onCancel={chat.cancel}
          />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-surface border-t border-surface-border">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me to transfer money, block a card, or show your balance..."
              className="w-full bg-black/50 border border-surface-border text-white text-sm rounded-xl px-4 py-4 pr-12 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-all placeholder-gray-600"
            />
            <button
              type="submit"
              aria-label="Send"
              disabled={!input.trim() || chat.isTyping}
              className="absolute right-2 p-2 bg-white text-black rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:hover:bg-white transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-[10px] text-gray-600 uppercase tracking-wider font-medium">NexusBank AI Assistant can make mistakes. Consider verifying important information.</p>
          </div>
        </div>
      </div>

    </div>
  );
}
