"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Receipt } from "lucide-react";
import { TransactionRows } from "@/components/ToolResultView";
import { fetchAccountTransactions, fetchAccounts } from "@/lib/banking";
import { label, maskNumber, money } from "@/lib/format";
import type { Account, Transaction } from "@/lib/types";

export default function TransactionsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [loadingTx, setLoadingTx] = useState(false);
  const [error, setError] = useState("");

  // Called from event handlers / promise callbacks, never directly in an effect body.
  const selectAccount = useCallback((accountId: string) => {
    setSelected(accountId);
    setLoadingTx(true);
    return fetchAccountTransactions(accountId)
      .then(data => {
        setTransactions(data ?? []);
        setError(data ? "" : "Could not load transactions.");
      })
      .catch(() => setError("Could not load transactions."))
      .finally(() => setLoadingTx(false));
  }, []);

  useEffect(() => {
    fetchAccounts()
      .then(data => {
        if (data) {
          setAccounts(data);
          if (data.length) selectAccount(data[0].id);
        } else {
          setError("Could not load your accounts.");
        }
      })
      .catch(() => setError("Could not load your accounts."))
      .finally(() => setLoadingAccounts(false));
  }, [selectAccount]);

  const account = accounts.find(a => a.id === selected);

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Transactions</h1>
        <p className="text-sm text-gray-400 mt-1">Recent activity on each of your accounts.</p>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {loadingAccounts ? (
        <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
      ) : (
        <div className="flex flex-wrap gap-3" role="tablist" aria-label="Accounts">
          {accounts.map(acc => (
            <button
              key={acc.id}
              type="button"
              role="tab"
              aria-selected={acc.id === selected}
              onClick={() => { if (acc.id !== selected) selectAccount(acc.id); }}
              className={`px-4 py-3 rounded-xl border text-left transition-colors ${
                acc.id === selected
                  ? "border-primary-500 bg-primary-500/10"
                  : "border-surface-border bg-surface hover:bg-surface-hover"
              }`}
            >
              <p className="text-sm text-white">{label(acc.account_type)}</p>
              <p className="text-xs font-mono text-gray-500">{maskNumber(acc.account_number)}</p>
            </button>
          ))}
        </div>
      )}

      {account && (
        <div className="glass-panel rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Receipt className="w-5 h-5 text-green-400" />
              <h2 className="text-lg font-semibold text-white">
                {label(account.account_type)} <span className="font-mono text-gray-500 text-sm">{maskNumber(account.account_number)}</span>
              </h2>
            </div>
            <p className="text-sm text-gray-400">Balance <span className="text-white font-medium">{money(account.current_balance, account.currency)}</span></p>
          </div>

          {loadingTx ? (
            <div className="h-24 flex items-center justify-center"><Loader2 className="w-5 h-5 animate-spin text-primary-500" /></div>
          ) : transactions.length === 0 ? (
            <p className="text-sm text-gray-500">No recent transactions.</p>
          ) : (
            <div className="text-sm">
              <TransactionRows transactions={transactions} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
