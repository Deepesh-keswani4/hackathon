import React, { useState } from "react";
import GlassCard from "../ui/GlassCard";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api";

interface Props {
  token: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function WFHForm({ token, onSuccess, onCancel }: Props) {
  const [form, setForm] = useState({ from_date: "", to_date: "", reason: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split("T")[0];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/attendance/wfh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          from_date: form.from_date,
          to_date: form.to_date || form.from_date,
          reason: form.reason,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.detail || "Failed");
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GlassCard className="max-w-md w-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900">WFH Request</h3>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-700 text-xl">✕</button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-600 block mb-1.5">From Date</label>
            <input
              type="date"
              required
              min={minDate}
              value={form.from_date}
              onChange={e => setForm(f => ({ ...f, from_date: e.target.value }))}
              className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm focus:outline-none focus:border-gray-400 transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-600 block mb-1.5">To Date</label>
            <input
              type="date"
              min={form.from_date || minDate}
              value={form.to_date}
              onChange={e => setForm(f => ({ ...f, to_date: e.target.value }))}
              className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm focus:outline-none focus:border-gray-400 transition-all"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-600 block mb-1.5">Reason</label>
          <textarea
            required
            rows={3}
            value={form.reason}
            onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
            placeholder="Reason for working from home..."
            className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm resize-none focus:outline-none focus:border-gray-400 transition-all"
          />
        </div>

        {error && (
          <div className="px-3 py-2 rounded-2xl bg-red-50 border border-red-100 text-sm text-red-600">{error}</div>
        )}

        <div className="flex gap-3">
          <button type="button" onClick={onCancel} className="flex-1 py-2.5 rounded-full border border-gray-200 text-sm font-semibold text-gray-600 hover:border-gray-400 transition-all">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="flex-1 py-2.5 rounded-full bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 transition-all disabled:opacity-50">
            {loading ? "Submitting..." : "Apply WFH ↗"}
          </button>
        </div>
      </form>
    </GlassCard>
  );
}
