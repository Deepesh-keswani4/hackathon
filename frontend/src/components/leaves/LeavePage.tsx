import React, { useEffect, useState } from "react";
import ApplyLeaveForm from "./ApplyLeaveForm";
import LeaveTable from "./LeaveTable";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api";

interface LeavePageProps {
  token: string;
  role: string;
}

interface LeaveBalance {
  casual_remaining: number;
  privilege_remaining: number;
  sick_remaining: number;
  comp_off_remaining: number;
}

interface Leave {
  id: number;
  leave_type: string;
  from_date: string;
  to_date: string;
  days_count: number;
  status: string;
  reason: string;
  is_half_day?: boolean;
  employee_name?: string;
}

type Tab = "mine" | "pending" | "history";

async function apiFetch(token: string, path: string) {
  const res = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return null;
  return res.json();
}

async function apiPost(token: string, path: string, body?: unknown) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

function ProgressBar({ value, max, color = "#E8D44D" }: { value: number; max: number; color?: string }) {
  const pct = Math.min(100, (value / Math.max(max, 1)) * 100);
  return (
    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mt-2">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export default function LeavePage({ token, role }: LeavePageProps) {
  const isManager = ["manager", "hr", "cfo", "admin"].includes(role);
  const [tab, setTab] = useState<Tab>("mine");
  const [showForm, setShowForm] = useState(false);
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [myLeaves, setMyLeaves] = useState<Leave[]>([]);
  const [pendingLeaves, setPendingLeaves] = useState<Leave[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  async function load() {
    setLoading(true);
    const [bal, mine, pending] = await Promise.all([
      apiFetch(token, "/leaves/balance/"),
      apiFetch(token, "/leaves/"),
      isManager ? apiFetch(token, "/leaves/?status=PENDING") : Promise.resolve(null),
    ]);
    if (bal) setBalance(bal);
    const myList = mine?.results ?? (Array.isArray(mine) ? mine : []);
    setMyLeaves(myList);
    if (pending) {
      const pList = pending?.results ?? (Array.isArray(pending) ? pending : []);
      setPendingLeaves(pList);
    }
    setLoading(false);
  }

  useEffect(() => { load(); }, [token]);

  async function handleApprove(id: number) {
    await apiPost(token, `/leaves/${id}/approve/`);
    showToast("Leave approved ✓");
    load();
  }

  async function handleReject(id: number) {
    const reason = prompt("Reason for rejection (optional):") ?? "";
    await apiPost(token, `/leaves/${id}/reject/`, { reason });
    showToast("Leave rejected");
    load();
  }

  async function handleCancel(id: number) {
    if (!confirm("Cancel this leave request?")) return;
    await fetch(`${BASE}/leaves/${id}/cancel/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    showToast("Leave cancelled");
    load();
  }

  const BALANCE_TILES = [
    { label: "Casual Leave", value: balance?.casual_remaining ?? 0, max: 6, color: "#E8D44D", dark: false },
    { label: "Privilege Leave", value: balance?.privilege_remaining ?? 0, max: 18, color: "#111111", dark: true },
    { label: "Sick Leave", value: balance?.sick_remaining ?? 0, max: 6, color: "#F87171", dark: false },
    { label: "Comp Off", value: balance?.comp_off_remaining ?? 0, max: 10, color: "#34D399", dark: false },
  ];

  const TABS: { id: Tab; label: string; count?: number }[] = [
    { id: "mine", label: "My Leaves" },
    ...(isManager ? [{ id: "pending" as Tab, label: "Pending", count: pendingLeaves.length }] : []),
    { id: "history", label: "History" },
  ];

  return (
    <div className="h-full overflow-y-auto p-5" style={{ background: "#EBF9F6" }}>
      {toast && (
        <div className="fixed top-5 right-5 z-50 px-4 py-3 bg-[#111111] text-white text-sm font-semibold rounded-2xl shadow-2xl">
          {toast}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <ApplyLeaveForm
            token={token}
            onSuccess={() => { setShowForm(false); showToast("Leave applied successfully ✓"); load(); }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-[#111111]">Leave Management</h2>
          <p className="text-xs text-gray-400 mt-0.5">Manage your time off requests</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-[#111111] text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-colors shadow-sm"
        >
          <span className="text-lg leading-none">+</span>
          <span>Apply Leave</span>
        </button>
      </div>

      {/* Balance tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {BALANCE_TILES.map(b => (
          <div
            key={b.label}
            className="rounded-2xl p-5 shadow-[0_1px_4px_rgba(0,0,0,0.07)]"
            style={{ background: b.dark ? "#111111" : "#ffffff" }}
          >
            <div className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${b.dark ? "text-white/40" : "text-gray-400"}`}>{b.label}</div>
            <div className={`text-4xl font-bold ${b.dark ? "text-white" : "text-[#111111]"}`}>
              {loading ? "—" : b.value}
            </div>
            <div className={`text-[10px] mt-0.5 ${b.dark ? "text-white/30" : "text-gray-400"}`}>of {b.max} days</div>
            <ProgressBar value={loading ? 0 : b.value} max={b.max} color={b.dark ? "white" : b.color} />
          </div>
        ))}
      </div>

      {/* Main table card */}
      <div className="bg-white rounded-2xl shadow-[0_1px_4px_rgba(0,0,0,0.07)] overflow-hidden">
        {/* Tab header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
          <div className="flex items-center gap-1 bg-gray-100 rounded-full p-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  tab === t.id ? "bg-[#111111] text-white shadow-sm" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {t.label}
                {t.count ? (
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${tab === t.id ? "bg-white/20 text-white" : "bg-gray-300 text-gray-600"}`}>
                    {t.count}
                  </span>
                ) : null}
              </button>
            ))}
          </div>
        </div>

        <div className="p-5">
          {tab === "mine" && (
            <LeaveTable leaves={myLeaves.filter(l => l.status === "PENDING")} loading={loading} onCancel={handleCancel} />
          )}
          {tab === "pending" && isManager && (
            <LeaveTable leaves={pendingLeaves} loading={loading} isManager onApprove={handleApprove} onReject={handleReject} />
          )}
          {tab === "history" && (
            <LeaveTable leaves={myLeaves.filter(l => l.status !== "PENDING")} loading={loading} />
          )}
        </div>
      </div>
    </div>
  );
}
