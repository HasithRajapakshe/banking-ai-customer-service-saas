// Display helpers. Never render full account/card numbers or internal IDs.

/** "1000200030004" -> "•••• 0004"; "6768" -> "•••• 6768". */
export function maskNumber(value: string | number | null | undefined): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  return digits ? `•••• ${digits.slice(-4)}` : "••••";
}

/** "1208577.7500", "LKR" -> "LKR 1,208,577.75" */
export function money(amount: string | number | null | undefined, currency?: string | null): string {
  const n = typeof amount === "number" ? amount : parseFloat(String(amount ?? ""));
  if (Number.isNaN(n)) return "—";
  const formatted = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return currency ? `${currency} ${formatted}` : formatted;
}

/** ISO timestamp -> "18 Oct 2026" (date only; no times or zones in lists). */
export function shortDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/** "fixed_deposit" -> "Fixed deposit" */
export function label(value: string | null | undefined): string {
  if (!value) return "—";
  const text = value.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
