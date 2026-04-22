import React, { useEffect, useState } from "react";
import RegularizationForm from "./RegularizationForm";
import WFHForm from "./WFHForm";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api";

interface AttendancePageProps {
  token: string;
  role: string;
}

interface AttendanceLog {
  id: number;
  date: string;
  status: string;
  check_in: string | null;
  check_out: string | null;
}

interface Regularization {
  id: number;
  date: string;
  status: string;
  requested_check_in: string | null;
  requested_check_out: string | null;
  reason: string;
  employee_name?: string;
}

interface WFHRequest {
  id: number;
  dates: string[];
  status: string;
  reason: string;
  employee_name?: string;
}

interface Penalty {
  id: number;
  date: string;
  penalty_type: string;
  days_deducted: number;
  status: string;
  reason: string;
}

type Tab = "logs" | "regularization" | "wfh" | "penalties";

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  PRESENT:     { bg: "#DCFCE7", text: "#15803D", label: "Present" },
  ABSENT:      { bg: "#FEE2E2", text: "#DC2626", label: "Absent" },
  WFH:         { bg: "#DBEAFE", text: "#1D4ED8", label: "WFH" },
  ON_LEAVE:    { bg: "#F3E8FF", text: "#7C3AED", label: "On Leave" },
  REGULARIZED: { bg: "#CCFBF1", text: "#0F766E", label: "Regularized" },
  WFH_PENDING: { bg: "#FEF9C3", text: "#854D0E", label: "WFH Pending" },
  HALF_DAY:    { bg: "#FFEDD5", text: "#C2410C", label: "Half Day" },
};

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

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { bg: "#F3F4F6", text: "#6B7280", label: status };
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: cfg.bg, color: cfg.text }}>
      {cfg.label}
    </span>
  );
}

export default function AttendancePage({ token, role }: AttendancePageProps) {
  const isManager = ["manager", "hr", "cfo", "admin"].includes(role);
  const [tab, setTab] = useState<Tab>("logs");
  const [logs, setLogs] = useState<AttendanceLog[]>([]);
  const [regularizations, setRegularizations] = useState<Regularization[]>([]);
  const [wfhRequests, setWfhRequests] = useState<WFHRequest[]>([]);
  const [penalties, setPenalties] = useState<Penalty[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRegForm, setShowRegForm] = useState(false);
  const [showWFHForm, setShowWFHForm] = useState(false);
  const [toast, setToast] = useState("");

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  async function load() {
    setLoading(true);
    const [logsData, regsData, wfhData, penData] = await Promise.all([
      apiFetch(token, "/attendance/logs/?limit=30"),
      apiFetch(token, "/attendance/regularization/"),
      apiFetch(token, "/attendance/wfh/"),
      apiFetch(token, "/attendance/penalties/"),
    ]);
    const toArr = (d: unknown) => Array.isArray(d) ? d : (d as { results?: unknown[] })?.results ?? [];
    setLogs(toArr(logsData));
    setRegularizations(toArr(regsData));
    setWfhRequests(toArr(wfhData));
    setPenalties(toArr(penData));
    setLoading(false);
  }

  useEffect(() => { load(); }, [token]);

  async function handleApproveReg(id: number) { await apiPost(token, `/attendance/regularization/${id}/approve/`); showToast("Regularization approved ✓"); load(); }
  async function handleRejectReg(id: number) { const r = prompt("Reason:") ?? ""; await apiPost(token, `/attendance/regularization/${id}/reject/`, { reason: r }); showToast("Rejected"); load(); }
  async function handleApproveWFH(id: number) { await apiPost(token, `/attendance/wfh/${id}/approve/`); showToast("WFH approved ✓"); load(); }
  async function handleRejectWFH(id: number) { await apiPost(token, `/attendance/wfh/${id}/reject/`, { reason: "Not approved" }); showToast("WFH rejected"); load(); }

  const todayStr = new Date().toISOString().split("T")[0];
  const todayLog = logs.find(l => l.date === todayStr);
  const presentCount = logs.filter(l => l.status === "PRESENT").length;
  const absentCount = logs.filter(l => l.status === "ABSENT").length;
  const wfhCount = logs.filter(l => l.status === "WFH").length;

  const TABS: { id: Tab; label: string }[] = [
    { id: "logs", label: "Logs" },
    { id: "regularization", label: "Regularization" },
    { id: "wfh", label: "WFH" },
    { id: "penalties", label: "Penalties" },
  ];

  return (
    <div className="h-full overflow-y-auto p-5" style={{ background: "#EDECEA" }}>
      {toast && (
        <div className="fixed top-5 right-5 z-50 px-4 py-3 bg-[#111111] text-white text-sm font-semibold rounded-2xl shadow-2xl">
          {toast}
        </div>
      )}

      {showRegForm && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <RegularizationForm token={token} onSuccess={() => { setShowRegForm(false); showToast("Regularization submitted ✓"); load(); }} onCancel={() => setShowRegForm(false)} />
        </div>
      )}
      {showWFHForm && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <WFHForm token={token} onSuccess={() => { setShowWFHForm(false); showToast("WFH request submitted ✓"); load(); }} onCancel={() => setShowWFHForm(false)} />
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-[#111111]">Attendance</h2>
          <p className="text-xs text-gray-400 mt-0.5">Track and manage attendance records</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowWFHForm(true)} className="px-4 py-2.5 bg-white text-[#111111] text-sm font-semibold rounded-full hover:bg-gray-50 transition-colors shadow-sm border border-gray-100">
            Apply WFH
          </button>
          <button onClick={() => setShowRegForm(true)} className="px-4 py-2.5 bg-[#111111] text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-colors shadow-sm">
            Regularize
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {/* Today's status */}
        <div className="col-span-2 bg-[#111111] rounded-2xl p-5 shadow-[0_1px_4px_rgba(0,0,0,0.07)]">
          <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-2">Today · {todayStr}</div>
          {todayLog ? (
            <>
              <StatusBadge status={todayLog.status} />
              {todayLog.check_in && (
                <div className="text-xs text-white/50 mt-3">
                  Check-in: {todayLog.check_in}{todayLog.check_out ? ` · Check-out: ${todayLog.check_out}` : " · Still in"}
                </div>
              )}
            </>
          ) : (
            <div className="text-sm text-white/60">No log recorded yet</div>
          )}
        </div>

        <div className="bg-[#E8D44D] rounded-2xl p-5 shadow-[0_1px_4px_rgba(0,0,0,0.07)]">
          <div className="text-[10px] font-semibold text-[#111111]/50 uppercase tracking-wider mb-1">Present</div>
          <div className="text-4xl font-bold text-[#111111]">{presentCount}</div>
          <div className="text-[10px] text-[#111111]/50 mt-0.5">last 30 days</div>
        </div>

        <div className="bg-white rounded-2xl p-5 shadow-[0_1px_4px_rgba(0,0,0,0.07)]">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">WFH</div>
          <div className="text-4xl font-bold text-[#111111]">{wfhCount}</div>
          <div className="text-[10px] text-gray-400 mt-0.5">last 30 days</div>
        </div>
      </div>

      {/* Main table */}
      <div className="bg-white rounded-2xl shadow-[0_1px_4px_rgba(0,0,0,0.07)] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
          <div className="flex items-center gap-1 bg-gray-100 rounded-full p-1">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                  tab === t.id ? "bg-[#111111] text-white shadow-sm" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-5">
          {loading ? (
            <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-12 rounded-xl bg-gray-50 animate-pulse" />)}</div>
          ) : (
            <>
              {tab === "logs" && (
                <div className="space-y-1">
                  {logs.length === 0 && <div className="py-12 text-center text-gray-400 text-sm">No attendance logs found</div>}
                  {logs.map(log => (
                    <div key={log.id} className="flex items-center gap-4 py-3 px-3 rounded-xl hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                      <div className="text-xs font-mono text-gray-500 w-24 flex-shrink-0">{log.date}</div>
                      <StatusBadge status={log.status} />
                      <div className="text-xs text-gray-400 ml-auto font-mono">
                        {log.check_in ? `In: ${log.check_in}` : "—"}
                        {log.check_out ? ` → ${log.check_out}` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {tab === "regularization" && (
                <div className="space-y-1">
                  {regularizations.length === 0 && <div className="py-12 text-center text-gray-400 text-sm">No regularization requests</div>}
                  {regularizations.map(r => (
                    <div key={r.id} className="flex items-center gap-4 py-3 px-3 rounded-xl hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0 group">
                      <div className="flex-1 min-w-0">
                        {isManager && r.employee_name && <div className="text-xs font-bold text-gray-900 mb-0.5">{r.employee_name}</div>}
                        <div className="text-sm font-medium text-gray-700">{r.date}</div>
                        <div className="text-xs text-gray-400 truncate">{r.reason}</div>
                      </div>
                      {r.requested_check_out && <div className="text-xs text-gray-400 font-mono">Out: {r.requested_check_out}</div>}
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${
                        r.status === "PENDING" ? "bg-yellow-100 text-yellow-800" :
                        r.status === "APPROVED" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"
                      }`}>{r.status}</span>
                      {isManager && r.status === "PENDING" && (
                        <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleApproveReg(r.id)} className="px-3 py-1 bg-[#111111] text-white text-[10px] font-semibold rounded-full">Approve</button>
                          <button onClick={() => handleRejectReg(r.id)} className="px-3 py-1 bg-red-500 text-white text-[10px] font-semibold rounded-full">Reject</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {tab === "wfh" && (
                <div className="space-y-1">
                  {wfhRequests.length === 0 && <div className="py-12 text-center text-gray-400 text-sm">No WFH requests</div>}
                  {wfhRequests.map(w => (
                    <div key={w.id} className="flex items-center gap-4 py-3 px-3 rounded-xl hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0 group">
                      <div className="flex-1 min-w-0">
                        {isManager && w.employee_name && <div className="text-xs font-bold text-gray-900 mb-0.5">{w.employee_name}</div>}
                        <div className="text-xs font-medium text-gray-700">
                          {Array.isArray(w.dates) ? w.dates.slice(0, 3).join(", ") + (w.dates.length > 3 ? ` +${w.dates.length - 3}` : "") : w.dates}
                        </div>
                        <div className="text-xs text-gray-400 truncate">{w.reason}</div>
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${
                        w.status === "PENDING" ? "bg-yellow-100 text-yellow-800" :
                        w.status === "APPROVED" ? "bg-blue-100 text-blue-700" : "bg-red-100 text-red-600"
                      }`}>{w.status}</span>
                      {isManager && w.status === "PENDING" && (
                        <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleApproveWFH(w.id)} className="px-3 py-1 bg-[#111111] text-white text-[10px] font-semibold rounded-full">Approve</button>
                          <button onClick={() => handleRejectWFH(w.id)} className="px-3 py-1 bg-red-500 text-white text-[10px] font-semibold rounded-full">Reject</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {tab === "penalties" && (
                <div className="space-y-1">
                  {penalties.length === 0 && <div className="py-12 text-center text-gray-400 text-sm">No penalties — great work! 🎉</div>}
                  {penalties.map(p => (
                    <div key={p.id} className="flex items-center gap-4 py-3 px-3 rounded-xl hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-700">{p.date}</div>
                        <div className="text-xs text-gray-400 truncate">{p.reason}</div>
                      </div>
                      <div className="text-sm font-bold text-red-600 font-mono">-{p.days_deducted}d</div>
                      <div className="text-xs font-medium text-gray-500">{p.penalty_type}</div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        p.status === "ACTIVE" ? "bg-red-100 text-red-600" :
                        p.status === "REVERSED" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                      }`}>{p.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
