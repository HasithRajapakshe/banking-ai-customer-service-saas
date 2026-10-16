"use client";

import { useState } from "react";
import { Upload, FileText, Loader2, Search } from "lucide-react";

export default function AdminDashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8001/api/v1/admin/rag/documents", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
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

  return (
    <div className="flex flex-col h-full overflow-y-auto p-8 gap-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Admin Portal</h1>
        <p className="text-gray-400">Manage RAG knowledge base and view system statistics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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

        {/* Audit Logs Placeholder */}
        <div className="glass-panel p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-purple-400" />
            Audit Logs
          </h2>
          <div className="flex flex-col items-center justify-center h-64 border border-surface-border rounded-xl bg-surface/50 text-gray-500">
            <p>System audit logs will appear here.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
