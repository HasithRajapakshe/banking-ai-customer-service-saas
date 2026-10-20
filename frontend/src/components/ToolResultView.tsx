"use client";

import { CreditCard, Wallet, ArrowDownLeft, ArrowUpRight } from "lucide-react";
import { label, maskNumber, money, shortDate } from "@/lib/format";
import type { Account, Card, Transaction } from "@/lib/types";

// Renders known tool results as compact lists using an allow-list of fields.
// IDs (account/card/tenant/customer) are only ever used as React keys, never
// shown, and account/card numbers are masked to their last 4 digits.

type Props = { toolName?: string | null; data: unknown };

const asList = <T,>(data: unknown): T[] => (Array.isArray(data) ? (data as T[]) : []);

function StatusPill({ status }: { status: string }) {
  const ok = status === "active" || status === "completed";
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
      ok ? "border-green-500/30 text-green-400 bg-green-500/10" : "border-red-500/30 text-red-400 bg-red-500/10"
    }`}>
      {label(status)}
    </span>
  );
}

export function AccountRows({ accounts }: { accounts: Account[] }) {
  return (
    <ul className="divide-y divide-surface-border">
      {accounts.map(acc => (
        <li key={acc.id} className="flex items-center justify-between gap-4 py-2">
          <div className="flex items-center gap-2 min-w-0">
            <Wallet className="w-3.5 h-3.5 text-primary-400 shrink-0" />
            <span className="text-gray-200">{label(acc.account_type)}</span>
            <span className="font-mono text-gray-500">{maskNumber(acc.account_number)}</span>
          </div>
          <span className="font-medium text-white whitespace-nowrap">{money(acc.current_balance, acc.currency)}</span>
        </li>
      ))}
    </ul>
  );
}

export function CardRows({ cards }: { cards: Card[] }) {
  return (
    <ul className="divide-y divide-surface-border">
      {cards.map(card => (
        <li key={card.id} className="flex items-center justify-between gap-4 py-2">
          <div className="flex items-center gap-2">
            <CreditCard className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="text-gray-200">{label(card.card_type)} card</span>
            <span className="font-mono text-gray-500">{maskNumber(card.card_last4)}</span>
          </div>
          <StatusPill status={card.status} />
        </li>
      ))}
    </ul>
  );
}

export function TransactionRows({ transactions }: { transactions: Transaction[] }) {
  return (
    <ul className="divide-y divide-surface-border">
      {transactions.map(tx => {
        const credit = tx.direction === "credit";
        return (
          <li key={tx.id} className="flex items-center justify-between gap-4 py-2">
            <div className="flex items-center gap-2 min-w-0">
              {credit
                ? <ArrowDownLeft className="w-3.5 h-3.5 text-green-400 shrink-0" />
                : <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 shrink-0" />}
              <span className="text-gray-200 truncate">
                {tx.merchant_name || tx.description || label(tx.transaction_type)}
              </span>
            </div>
            <div className="flex items-center gap-3 whitespace-nowrap">
              <span className="text-gray-500">{shortDate(tx.transaction_at)}</span>
              <span className={`font-medium ${credit ? "text-green-400" : "text-white"}`}>
                {credit ? "+" : ""}{money(tx.amount, tx.currency)}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default function ToolResultView({ toolName, data }: Props) {
  let body: React.ReactNode = null;

  switch (toolName) {
    case "account.list": {
      const accounts = asList<Account>(data);
      if (accounts.length) body = <AccountRows accounts={accounts} />;
      break;
    }
    case "card.list": {
      const cards = asList<Card>(data);
      if (cards.length) body = <CardRows cards={cards} />;
      break;
    }
    case "card.get_details":
    case "card.block": {
      if (data && typeof data === "object" && !Array.isArray(data)) body = <CardRows cards={[data as Card]} />;
      break;
    }
    case "account.get_transactions":
    case "card.get_transactions": {
      const transactions = asList<Transaction>(data).slice(0, 10);
      if (transactions.length) body = <TransactionRows transactions={transactions} />;
      break;
    }
    // Anything else: the assistant's text already says what matters.
  }

  if (!body) return null;
  return (
    <div className="bg-black/30 border border-surface-border px-4 py-1 rounded-xl text-xs max-w-full">
      {body}
    </div>
  );
}
