// Read-only banking data for the dashboard pages (all via the API Gateway,
// which reads through the Tool Gateway with permission checks and audit).

import { apiFetch } from "@/lib/api";
import type { Account, Card, Transaction } from "@/lib/types";

async function getJson<T>(path: string): Promise<T | null> {
  const res = await apiFetch(path);
  return res.ok ? res.json() : null;
}

export const fetchAccounts = () => getJson<Account[]>("/api/v1/accounts");
export const fetchCards = () => getJson<Card[]>("/api/v1/cards");
export const fetchAccountTransactions = (accountId: string, limit = 20) =>
  getJson<Transaction[]>(`/api/v1/accounts/${encodeURIComponent(accountId)}/transactions?limit=${limit}`);
