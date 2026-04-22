import React, { useState } from "react";
import GlassCard from "../ui/GlassCard";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api";

interface ApplyLeaveFormProps {
  token: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const LEAVE_TYPES = [
  { value: "CL", label: "Casual Leave" },
  { value: "SL", label: "Sick Leave" },
  { value: "PL", label: "Privilege Leave" },
  { value: "LOP", label: "Loss of Pay" },
  { value: "CO", label: "Comp Off" },
];

export default function ApplyLeaveForm({ token, onSuccess, onCancel }: ApplyLeaveFormProps) {
  const [form, setForm] = useState({
    leave_type: "CL",
    from_date: "",
    to_date: "",
    is_half_day: false,
    half_day_period: "AM",
    reason: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        leave_type: form.leave_type,
        from_date: form.from_date,
        to_date: form.is_half_day ? form.from_date : form.to_date,
        reason: form.reason,
        is_half_day: form.is_half_day,
      };
      if (form.is_half_day) body.half_day_period = form.half_day_period;

      const res = await fetch(`${BASE}/leaves/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.detail || "Failed to apply leave");
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <GlassCard className="max-w-lg w-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-gray-900">Apply Leave</h3>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-700 text-xl">✕</button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-gray-600 block mb-1.5">Leave Type</label>
          <div className="flex flex-wrap gap-2">
            {LEAVE_TYPES.map(lt => (
              <button
                key={lt.value}
                type="button"
                onClick={() => setForm(f => ({ ...f, leave_type: lt.value }))}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                  form.leave_type === lt.value
                    ? "bg-gray-900 text-white"
                    : "bg-white/60 border border-gray-200 text-gray-600 hover:border-gray-400"
                }`}
              >
                {lt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <div
              onClick={() => setForm(f => ({ ...f, is_half_day: !f.is_half_day }))}
              className={`w-10 h-5 rounded-full transition-colors ${form.is_half_day ? "bg-gray-900" : "bg-gray-200"} relative`}
            >
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${form.is_half_day ? "left-5" : "left-0.5"}`} />
            </div>
            <span className="text-xs font-semibold text-gray-700">Half Day</span>
          </label>
          {form.is_half_day && (
            <div className="flex gap-2">
              {["AM", "PM"].map(p => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, half_day_period: p }))}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${form.half_day_period === p ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600"}`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-600 block mb-1.5">
              {form.is_half_day ? "Date" : "From Date"}
            </label>
            <input
              type="date"
              required
              value={form.from_date}
              onChange={e => setForm(f => ({ ...f, from_date: e.target.value }))}
              className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm text-gray-900 focus:outline-none focus:border-gray-400 focus:bg-white transition-all"
            />
          </div>
          {!form.is_half_day && (
            <div>
              <label className="text-xs font-semibold text-gray-600 block mb-1.5">To Date</label>
              <input
                type="date"
                required
                value={form.to_date}
                min={form.from_date}
                onChange={e => setForm(f => ({ ...f, to_date: e.target.value }))}
                className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm text-gray-900 focus:outline-none focus:border-gray-400 focus:bg-white transition-all"
              />
            </div>
          )}
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-600 block mb-1.5">Reason</label>
          <textarea
            required
            rows={3}
            value={form.reason}
            onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
            placeholder="Brief reason for leave..."
            className="w-full px-3 py-2.5 rounded-2xl bg-white/60 border border-gray-200 text-sm text-gray-900 focus:outline-none focus:border-gray-400 focus:bg-white transition-all resize-none"
          />
        </div>

        {error && (
          <div className="px-3 py-2 rounded-2xl bg-red-50 border border-red-100 text-sm text-red-600">{error}</div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-2.5 rounded-full border border-gray-200 text-sm font-semibold text-gray-600 hover:border-gray-400 transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-2.5 rounded-full bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 transition-all disabled:opacity-50"
          >
            {loading ? "Submitting..." : "Apply Leave ↗"}
          </button>
        </div>
      </form>
    </GlassCard>
  );
}
