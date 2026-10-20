"use client";

import { useCallback, useEffect, useState } from "react";
import { Upload, FileText, Loader2, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { AuditPage } from "@/lib/types";

const PAGE_SIZE = 15;

async function fetchAudit(offset: number): Promise<AuditPage | null> {
  const res = await apiFetch(`/api/v1/admin/audit?limit=${PAGE_SIZE}&offset=${offset}`);
  return res.ok ? res.json() : null;
}

export default function AdminDashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const [audit, setAudit] = useState<AuditPage | null>(null);
  const [auditError, setAuditError] = useState("");
  const [offset, setOffset] = useState(0);

  const loadAudit = useCallback((from: number) => {
    return fetchAudit(from)
      .then(page => {
        if (page) {
          setAudit(page);
          setAuditError("");
        } else {
          setAuditError("Could not load the audit log.");
        }
      })
      .catch(() => setAuditError("Could not load the audit log."));
  }, []);

  useEffect(() => {
    loadAudit(offset);
  }, [loadAudit, offset]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiFetch("/api/v1/admin/rag/documents", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        setMessage("Document uploaded and ingested successfully!");
        setFile(null);
      } else {
        setMessage("Failed to upload document.");
      }
    } catch {
      setMessage("Error uploading document.");
    } finally {
      setUploading(false);
    }
  };

  const total = audit?.total ?? 0;

  return (
    <div className="flex flex-col h-full overflow-y-auto p-8 gap-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Admin Portal</h1>
        <p className="text-gray-400">Manage RAG knowledge base and view system statistics.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* RAG Ingestion Card */}
        <div className="glass-panel p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-primary-400" />
            Knowledge Base Ingestion
          </h2>
          <p className="text-sm text-gray-400 mb-6">
            Upload PDF or Text documents to be embedded and added to the RAG knowledge base.
          </p>

          <form onSubmit={handleUpload} className="flex flex-col gap-4">
            <div className="border-2 border-dashed border-surface-border rounded-xl p-8 flex flex-col items-center justify-center bg-surface cursor-pointer hover:bg-surface-hover transition-colors">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="flex flex-col items-center cursor-pointer">
                <FileText className="w-10 h-10 text-gray-400 mb-2" />
                <span className="text-white font-medium">
                  {file ? file.name : "Select a document to upload"}
                </span>
                <span className="text-xs text-gray-500 mt-1">Supports PDF and TXT files</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={!file || uploading}
              className="bg-primary-600 hover:bg-primary-500 text-white font-semibold py-3 px-4 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                "Ingest Document"
              )}
            </button>

            {message && (
              <p className={`text-sm text-center ${message.includes("Error") || message.includes("Failed") ? "text-red-400" : "text-green-400"}`}>
                {message}
              </p>
            )}
          </form>
        </div>

        {/* Audit log */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col min-w-0">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-purple-400" />
            Audit Log
            {audit && <span className="text-sm font-normal text-gray-500">({total} entries)</span>}
          </h2>

          {auditError && <p className="text-sm text-red-400 mb-3">{auditError}</p>}
          {!audit && !auditError && (
            <div className="flex items-center justify-center h-40"><Loader2 className="w-6 h-6 animate-spin text-primary-500" /></div>
          )}

          {audit && (
            <>
              <div className="overflow-x-auto border border-surface-border rounded-xl">
                <table className="w-full text-xs text-left">
                  <thead className="bg-surface text-gray-400">
                    <tr>
                      <th className="px-3 py-2 font-medium">Time</th>
                      <th className="px-3 py-2 font-medium">Action</th>
                      <th className="px-3 py-2 font-medium">Tool</th>
                      <th className="px-3 py-2 font-medium">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border text-gray-300">
                    {audit.items.length === 0 && (
                      <tr><td colSpan={4} className="px-3 py-6 text-center text-gray-500">No audit entries yet.</td></tr>
                    )}
                    {audit.items.map(item => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 whitespace-nowrap">{new Date(item.created_at).toLocaleString()}</td>
                        <td className="px-3 py-2 font-mono">{item.action}</td>
                        <td className="px-3 py-2 font-mono">{String(item.metadata.tool_name ?? item.resource_type ?? "—")}</td>
                        <td className={`px-3 py-2 ${item.success ? "text-green-400" : "text-red-400"}`}>
                          {item.success ? "ok" : String(item.metadata.error_code ?? "failed")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                <span>
                  {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    aria-label="Previous page"
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                    className="p-1.5 rounded-lg border border-surface-border disabled:opacity-40 hover:bg-white/5"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    aria-label="Next page"
                    disabled={offset + PAGE_SIZE >= total}
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    className="p-1.5 rounded-lg border border-surface-border disabled:opacity-40 hover:bg-white/5"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
