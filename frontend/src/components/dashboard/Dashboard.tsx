import React, { useEffect, useState, useRef } from "react";
import { NavPage } from "../layout/Sidebar";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api";

interface DashboardProps {
  token: string;
  role: string;
  userName: string;
  onNav: (p: NavPage) => void;
}

interface LeaveBalance {
  casual_remaining: number;
  privilege_remaining: number;
  sick_remaining: number;
  comp_off_remaining: number;
}

interface PendingLeave {
  id: number;
  employee_name: string;
  leave_type: string;
  days_count: number;
  from_date: string;
  reason?: string;
}

interface Employee {
  id: number;
  employee_id: string;
  user?: { name?: string; email?: string };
  role: string;
  title?: string;
  department?: { name: string };
  is_active: boolean;
}

async function apiFetch(token: string, path: string) {
  try {
    const res = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function apiPost(token: string, path: string, body?: unknown) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

// ── Donut timer ────────────────────────────────────────────────────────────────
function DonutTimer() {
  const [seconds, setSeconds] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => setSeconds(s => s + 1), 1000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [running]);

  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const display = `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;

  // SVG donut
  const r = 52;
  const circ = 2 * Math.PI * r;
  const maxSecs = 28800; // 8 hours
  const pct = Math.min(seconds / maxSecs, 1);
  const offset = circ * (1 - pct);

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg width="128" height="128" viewBox="0 0 128 128" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="64" cy="64" r={r} fill="none" stroke="#F2EDE0" strokeWidth="10" />
          <circle
            cx="64" cy="64" r={r} fill="none"
            stroke="#F5D547" strokeWidth="10"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 1s linear" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold" style={{ color: "#1A1A1A" }}>{display}</div>
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mt-0.5">Work Time</div>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-4">
        <button
          onClick={() => setRunning(v => !v)}
          className="w-9 h-9 rounded-full flex items-center justify-center transition-all hover:opacity-80"
          style={{ background: "#F5D547" }}
        >
          {running ? (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#1A1A1A"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#1A1A1A"><polygon points="5,3 19,12 5,21"/></svg>
          )}
        </button>
        <button
          onClick={() => { setSeconds(0); setRunning(false); }}
          className="w-9 h-9 rounded-full flex items-center justify-center transition-all hover:opacity-80"
          style={{ background: "#F2EDE0" }}
        >
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" stroke="#6B6B6B" strokeWidth="2" strokeLinecap="round"/><path d="M3 3v5h5" stroke="#6B6B6B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
      </div>
    </div>
  );
}

// ── Mini bar chart ─────────────────────────────────────────────────────────────
function WeeklyBarChart({ presentCount }: { presentCount: number }) {
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const today = new Date().getDay(); // 0=Sun
  const todayIdx = today === 0 ? 6 : today - 1;
  // Mock weekly bars based on present count
  const values = [65, 80, 55, 90, 70, 30, 20].map((v, i) => i < todayIdx ? v : i === todayIdx ? Math.min(presentCount * 10 + 60, 95) : 15);

  return (
    <div className="flex items-end gap-1.5 h-20 mt-3">
      {days.map((d, i) => {
        const isToday = i === todayIdx;
        const h = values[i];
        return (
          <div key={i} className="flex flex-col items-center gap-1 flex-1">
            <div
              className="w-full rounded-sm transition-all"
              style={{
                height: `${h}%`,
                background: isToday ? "#F5D547" : "#E8E3D8",
                minHeight: "4px",
                maxHeight: "64px",
              }}
            />
            <div className="text-[10px] font-medium" style={{ color: isToday ? "#1A1A1A" : "#9B9B9B" }}>{d}</div>
          </div>
        );
      })}
    </div>
  );
}

// ── Progress bar ───────────────────────────────────────────────────────────────
function ThinBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min(100, (value / Math.max(max, 1)) * 100);
  return (
    <div className="h-1 rounded-full overflow-hidden" style={{ background: "#F0EBE0" }}>
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

// ── Avatar initials ────────────────────────────────────────────────────────────
const AVATAR_COLORS = ["#F5D547", "#1A1A1A", "#34D399", "#F87171", "#60A5FA", "#F472B6", "#A78BFA"];
function Avatar({ name, size = 36, idx = 0 }: { name: string; size?: number; idx?: number }) {
  const initials = name.split(" ").filter(Boolean).map(w => w[0].toUpperCase()).slice(0, 2).join("");
  const bg = AVATAR_COLORS[idx % AVATAR_COLORS.length];
  const color = bg === "#1A1A1A" || bg === "#F472B6" || bg === "#A78BFA" || bg === "#60A5FA" ? "#FFFFFF" : "#1A1A1A";
  return (
    <div
      className="rounded-full flex items-center justify-center font-bold flex-shrink-0"
      style={{ width: size, height: size, background: bg, color, fontSize: size * 0.35 }}
    >
      {initials || "?"}
    </div>
  );
}

export default function Dashboard({ token, role, userName, onNav }: DashboardProps) {
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [pendingLeaves, setPendingLeaves] = useState<PendingLeave[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");

  const firstName = userName.split(" ")[0] || "there";
  const isManager = ["manager", "hr", "cfo", "admin"].includes(role);

  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long" });

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [bal, pending, emps] = await Promise.all([
        apiFetch(token, "/leaves/balance/"),
        isManager ? apiFetch(token, "/leaves/?status=PENDING&limit=10") : Promise.resolve(null),
        apiFetch(token, "/employees/?page_size=8"),
      ]);
      if (bal) setBalance(bal);
      if (pending) {
        const list = pending?.results ?? (Array.isArray(pending) ? pending : []);
        setPendingLeaves(list.slice(0, 8));
      }
      if (emps) {
        const list = emps?.results ?? (Array.isArray(emps) ? emps : []);
        setEmployees(list.slice(0, 8));
      }
      setLoading(false);
    }
    load();
  }, [token]);

  async function handleApprove(id: number) {
    await apiPost(token, `/leaves/${id}/approve/`);
    showToast("Leave approved ✓");
    setPendingLeaves(prev => prev.filter(l => l.id !== id));
  }

  async function handleReject(id: number) {
    await apiPost(token, `/leaves/${id}/reject/`, { reason: "Declined by manager" });
    showToast("Leave rejected");
    setPendingLeaves(prev => prev.filter(l => l.id !== id));
  }

  const totalLeave = (balance?.casual_remaining ?? 0) + (balance?.privilege_remaining ?? 0) + (balance?.sick_remaining ?? 0);
  const presentPct = 78;
  const leavePct = 12;
  const wfhPct = 45;
  const attendPct = 92;

  // People today status mock derived from employees
  const statuses = ["In office", "WFH", "On leave", "In office", "In office", "WFH", "In office", "WFH"];
  const statusColors = { "In office": "#34D399", "WFH": "#F5D547", "On leave": "#F87171" };

  return (
    <div className="min-h-full p-5" style={{ background: "#EEEADE" }}>
      {toast && (
        <div className="fixed top-4 right-4 z-50 px-4 py-3 rounded-xl text-sm font-semibold shadow-xl" style={{ background: "#1A1A1A", color: "#FFFFFF" }}>
          {toast}
        </div>
      )}

      {/* ── HERO WELCOME BANNER ─────────────────────────────────────────────── */}
      <div
        className="w-full rounded-2xl p-8 mb-5 relative overflow-hidden"
        style={{ background: "#F5D95A" }}
      >
        <div className="flex items-start justify-between">
          {/* Left: greeting */}
          <div className="flex-1">
            <p className="text-sm font-medium mb-1" style={{ color: "rgba(26,26,26,0.6)" }}>{dateStr}</p>
            <h1 className="text-3xl font-bold mb-1" style={{ color: "#1A1A1A", letterSpacing: "-0.02em" }}>
              Welcome back, <em style={{ fontStyle: "italic", fontWeight: 700 }}>{firstName}</em>
            </h1>
            <p className="text-sm" style={{ color: "rgba(26,26,26,0.6)" }}>
              Here's what's happening across your team today.
            </p>

            {/* Progress bars row */}
            <div className="grid grid-cols-4 gap-6 mt-6">
              {[
                { label: "Present", pct: presentPct, color: "#E8BE2A" },
                { label: "On Leave", pct: leavePct, color: "#E8BE2A" },
                { label: "WFH", pct: wfhPct, color: "#1A1A1A" },
                { label: "Attendance", pct: attendPct, color: "#34D399" },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium" style={{ color: "rgba(26,26,26,0.7)" }}>{item.label}</span>
                    <span className="text-xs font-bold" style={{ color: "#1A1A1A" }}>{item.pct}%</span>
                  </div>
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(26,26,26,0.15)" }}>
                    <div className="h-full rounded-full" style={{ width: `${item.pct}%`, background: item.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: stat chips */}
          <div className="flex items-center gap-4 ml-8 flex-shrink-0">
            {[
              { icon: "👤", value: employees.length || 78, label: "Employees" },
              { icon: "👥", value: Math.floor((employees.length || 56) * 0.7), label: "Active Today" },
              { icon: "📁", value: 203, label: "Projects" },
            ].map(s => (
              <div key={s.label} className="flex items-center gap-2.5">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
                  style={{ background: "rgba(255,255,255,0.5)" }}
                >
                  {s.icon}
                </div>
                <div>
                  <div className="text-2xl font-bold leading-none" style={{ color: "#1A1A1A" }}>{s.value}</div>
                  <div className="text-xs mt-0.5" style={{ color: "rgba(26,26,26,0.6)" }}>{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── BENTO CARDS ROW ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-4 mb-4">

        {/* 1. Profile card */}
        <div
          className="relative rounded-2xl overflow-hidden cursor-pointer group"
          style={{ height: "240px", background: "#D4C5A0" }}
          onClick={() => onNav("employees")}
        >
          {/* Placeholder avatar illustration */}
          <div className="absolute inset-0 flex items-center justify-center" style={{ background: "linear-gradient(135deg, #C8B070 0%, #D4C5A0 60%, #E8D88A 100%)" }}>
            <div className="text-center">
              <div
                className="w-24 h-24 rounded-full mx-auto mb-2 flex items-center justify-center text-4xl font-bold"
                style={{ background: "rgba(255,255,255,0.3)", color: "#1A1A1A" }}
              >
                {firstName.slice(0, 1)}
              </div>
            </div>
          </div>
          {/* Arrow */}
          <div className="absolute top-3 right-3 w-7 h-7 rounded-full bg-white/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24"><path d="M7 17L17 7M17 7H7M17 7v10" stroke="#1A1A1A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
          {/* Bottom overlay */}
          <div
            className="absolute bottom-0 left-0 right-0 p-4"
            style={{ background: "linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 100%)" }}
          >
            <div className="text-white font-bold text-sm">{userName || "User"}</div>
            <div className="text-white/70 text-xs mt-0.5 capitalize">{role} · HRMS</div>
            <div className="mt-2">
              <span
                className="text-xs font-semibold px-2.5 py-0.5 rounded-full"
                style={{ background: "#F5D547", color: "#1A1A1A" }}
              >
                Active
              </span>
            </div>
          </div>
        </div>

        {/* 2. Progress card */}
        <div className="rounded-2xl p-5 bg-white" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-semibold" style={{ color: "#1A1A1A" }}>Progress</span>
            <button
              onClick={() => onNav("attendance")}
              className="w-6 h-6 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
            >
              <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M7 17L17 7M17 7H7M17 7v10" stroke="#6B6B6B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>
          <div className="text-xs text-gray-400 mb-1">Work Time</div>
          <div className="text-3xl font-bold" style={{ color: "#1A1A1A" }}>
            {loading ? "—" : "6.1h"}
          </div>
          <div className="text-xs text-gray-400">this week</div>
          <WeeklyBarChart presentCount={78} />
        </div>

        {/* 3. Time tracker card */}
        <div className="rounded-2xl p-5 bg-white" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <div className="flex items-center justify-between mb-1">
            <div>
              <div className="text-sm font-semibold" style={{ color: "#1A1A1A" }}>Time tracker</div>
              <div className="text-xs text-gray-400 mt-0.5">Today · Office</div>
            </div>
            <button
              onClick={() => onNav("attendance")}
              className="px-2.5 py-1 rounded-full text-xs font-semibold hover:opacity-80 transition-opacity"
              style={{ background: "#F5D547", color: "#1A1A1A" }}
            >
              Regularize
            </button>
          </div>
          <div className="flex justify-center mt-2">
            <DonutTimer />
          </div>
        </div>

        {/* 4. Leave balance card */}
        <div className="rounded-2xl p-5 bg-white" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold" style={{ color: "#1A1A1A" }}>Leave balance</span>
            <button
              onClick={() => onNav("leaves")}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold transition-all hover:opacity-80"
              style={{ background: "#F5D547", color: "#1A1A1A" }}
            >
              <span>+</span> Apply
            </button>
          </div>
          <div className="text-4xl font-bold mb-0.5" style={{ color: "#1A1A1A" }}>
            {loading ? "—" : totalLeave}
          </div>
          <div className="text-xs text-gray-400 mb-4">days remaining</div>

          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: "#1A1A1A" }}>Casual</span>
                <span className="text-xs text-gray-400">{loading ? "—" : balance?.casual_remaining ?? 0}/12</span>
              </div>
              <ThinBar value={balance?.casual_remaining ?? 0} max={12} color="#F5D547" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: "#1A1A1A" }}>Sick</span>
                <span className="text-xs text-gray-400">{loading ? "—" : balance?.sick_remaining ?? 0}/10</span>
              </div>
              <ThinBar value={balance?.sick_remaining ?? 0} max={10} color="#34D399" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: "#1A1A1A" }}>Earned</span>
                <span className="text-xs text-gray-400">{loading ? "—" : balance?.privilege_remaining ?? 0}/18</span>
              </div>
              <ThinBar value={balance?.privilege_remaining ?? 0} max={18} color="#1A1A1A" />
            </div>
          </div>
        </div>
      </div>

      {/* ── BOTTOM ROW ─────────────────────────────────────────────────────── */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 400px" }}>

        {/* People Today */}
        <div className="rounded-2xl p-5 bg-white" style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-semibold" style={{ color: "#1A1A1A" }}>People · Today</span>
            <button
              onClick={() => onNav("employees")}
              className="text-xs font-medium hover:underline"
              style={{ color: "#6B6B6B" }}
            >
              View all
            </button>
          </div>

          <div className="flex gap-3 overflow-x-auto pb-2" style={{ scrollbarWidth: "none" }}>
            {loading ? (
              [1,2,3,4,5,6].map(i => <div key={i} className="w-28 h-24 rounded-xl flex-shrink-0 animate-pulse" style={{ background: "#F2EDE0" }} />)
            ) : employees.length === 0 ? (
              <div className="text-sm text-gray-400 py-4">No employees found</div>
            ) : (
              employees.map((emp, idx) => {
                const name = emp.user?.name || emp.employee_id || "Unknown";
                const status = statuses[idx % statuses.length] as keyof typeof statusColors;
                const dotColor = statusColors[status] || "#9B9B9B";
                return (
                  <div
                    key={emp.id}
                    className="flex-shrink-0 rounded-xl p-3 flex flex-col items-start gap-1.5 cursor-pointer hover:shadow-md transition-all"
                    style={{ width: "112px", border: "1px solid #F0EBE0", background: "#FDFCF9" }}
                  >
                    <div className="relative">
                      <Avatar name={name} size={36} idx={idx} />
                      <div
                        className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white"
                        style={{ background: dotColor }}
                      />
                    </div>
                    <div>
                      <div className="text-xs font-semibold leading-tight truncate w-full" style={{ color: "#1A1A1A", maxWidth: "88px" }}>
                        {name.split(" ")[0]} {name.split(" ")[1]?.slice(0, 1) ? name.split(" ")[1].slice(0, 1) + "." : ""}
                      </div>
                      <div className="text-[10px] text-gray-400 truncate" style={{ maxWidth: "88px" }}>
                        {emp.department?.name || emp.title || emp.role}
                      </div>
                      <div className="text-[10px] font-medium mt-0.5" style={{ color: dotColor }}>
                        {status}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* WFH / Pending Requests dark panel */}
        <div
          className="rounded-2xl p-5 overflow-hidden"
          style={{ background: "#1C1C1C", boxShadow: "0 1px 4px rgba(0,0,0,0.15)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="white" strokeWidth="2"/><polyline points="9 22 9 12 15 12 15 22" stroke="white" strokeWidth="2"/></svg>
              <span className="text-sm font-semibold text-white">
                {isManager ? "Pending Approvals" : "WFH Requests"}
              </span>
            </div>
            {pendingLeaves.length > 0 && (
              <span
                className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{ background: "#F5D547", color: "#1A1A1A" }}
              >
                {pendingLeaves.length} pending
              </span>
            )}
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto pr-1" style={{ scrollbarWidth: "none" }}>
            {loading ? (
              [1,2,3].map(i => <div key={i} className="h-16 rounded-xl animate-pulse" style={{ background: "#2A2A2A" }} />)
            ) : pendingLeaves.length === 0 ? (
              <div className="text-sm text-center py-8" style={{ color: "rgba(255,255,255,0.3)" }}>
                No pending requests
              </div>
            ) : (
              pendingLeaves.map((leave, idx) => (
                <div key={leave.id} className="rounded-xl p-3" style={{ background: "#2A2A2A" }}>
                  <div className="flex items-start justify-between mb-2.5">
                    <div className="flex items-center gap-2.5">
                      <Avatar name={leave.employee_name || "?"} size={32} idx={idx} />
                      <div>
                        <div className="text-xs font-semibold text-white leading-tight">
                          {leave.employee_name || "Employee"}
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.4)" }}>
                          {leave.leave_type} · {leave.days_count}d
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.35)" }}>
                      {leave.from_date}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApprove(leave.id)}
                      className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs font-semibold transition-all hover:opacity-80"
                      style={{ background: "#F5D547", color: "#1A1A1A" }}
                    >
                      <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(leave.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:opacity-60"
                      style={{ color: "rgba(255,255,255,0.5)" }}
                    >
                      <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                      Decline
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {!isManager && (
            <button
              onClick={() => onNav("leaves")}
              className="w-full mt-3 py-2 rounded-xl text-xs font-semibold transition-all hover:opacity-80"
              style={{ background: "#F5D547", color: "#1A1A1A" }}
            >
              + Apply Leave
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
