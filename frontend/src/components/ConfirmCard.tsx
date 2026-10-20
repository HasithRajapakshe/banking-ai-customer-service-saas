"use client";

import { motion } from "framer-motion";
import { ShieldAlert } from "lucide-react";

type Props = {
  summary: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export default function ConfirmCard({ summary, onConfirm, onCancel }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      role="alertdialog"
      aria-labelledby="confirm-title"
      className="p-4 rounded-2xl border border-amber-500/40 bg-amber-500/10 space-y-3"
    >
      <div className="flex items-center gap-2 text-amber-300 text-sm font-semibold" id="confirm-title">
        <ShieldAlert className="w-4 h-4" /> Confirmation required
      </div>
      <p className="text-white text-sm">{summary}</p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="px-4 py-2 rounded-lg bg-amber-500 text-black text-sm font-semibold hover:bg-amber-400 transition-colors"
        >
          Confirm
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg border border-surface-border text-gray-300 text-sm hover:bg-white/5 transition-colors"
        >
          Cancel
        </button>
      </div>
    </motion.div>
  );
}
