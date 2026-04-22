import React, { useState } from "react";
import { NavPage } from "./Sidebar";

interface NotificationItem {
  id: number;
  subject: string;
  body: string;
  read: boolean;
  created_at: string;
  metadata?: Record<string, unknown>;
}

interface TopBarProps {
  page: NavPage;
  notifications: NotificationItem[];
  unreadCount: number;
  onMarkRead: (id: number) => void;
  onNav: (p: NavPage) => void;
  userName?: string;
  onLogout?: () => void;
}

const NAV_TABS: { id: NavPage; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "employees", label: "People" },
  { id: "leaves", label: "Leave" },
  { id: "attendance", label: "Attendance" },
  { id: "chat", label: "AI Assistant" },
];

export default function TopBar({ page, notifications, unreadCount, onMarkRead, onNav, userName = "", onLogout }: TopBarProps) {
  const [showNotifs, setShowNotifs] = useState(false);
  const initials = userName.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "HR";

  return (
    <header
      className="flex items-center justify-between px-6 flex-shrink-0"
      style={{
        background: "#FFFFFF",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
        height: "56px",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm"
          style={{ background: "#1A1A1A" }}
        >
          H
        </div>
        <span className="font-bold text-sm" style={{ color: "#1A1A1A", letterSpacing: "-0.01em" }}>
          Hivedesk
        </span>
      </div>

      {/* Centered nav */}
      <nav
        className="flex items-center rounded-full px-1.5 py-1.5 gap-0.5"
        style={{ background: "#F2EDE0", position: "absolute", left: "50%", transform: "translateX(-50%)" }}
      >
        {NAV_TABS.map(t => (
          <button
            key={t.id}
            onClick={() => onNav(t.id)}
            className="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200"
            style={{
              background: page === t.id ? "#1A1A1A" : "transparent",
              color: page === t.id ? "#FFFFFF" : "#6B6B6B",
              fontWeight: page === t.id ? 600 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Right actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Search */}
        <button className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors text-gray-500">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/><path d="M21 21l-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
        </button>

        {/* Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(v => !v)}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors text-gray-500 relative"
          >
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
            {unreadCount > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 w-4 h-4 text-white text-[9px] font-bold rounded-full flex items-center justify-center"
                style={{ background: "#F5D547", color: "#1A1A1A" }}
              >
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div
              className="absolute right-0 top-10 w-80 rounded-2xl overflow-hidden z-50"
              style={{ background: "#FFFFFF", boxShadow: "0 8px 32px rgba(0,0,0,0.12)", border: "1px solid rgba(0,0,0,0.06)" }}
            >
              <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid #F2EDE0" }}>
                <span className="font-semibold text-sm" style={{ color: "#1A1A1A" }}>Notifications</span>
                {unreadCount > 0 && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: "#F5D547", color: "#1A1A1A" }}>
                    {unreadCount} new
                  </span>
                )}
              </div>
              <div className="max-h-72 overflow-y-auto divide-y" style={{ borderColor: "#F2EDE0" }}>
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-gray-400">All caught up ✓</div>
                ) : (
                  notifications.map(n => (
                    <div
                      key={n.id}
                      onClick={() => { onMarkRead(n.id); setShowNotifs(false); }}
                      className="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
                      style={{ background: !n.read ? "#FFFDF0" : undefined }}
                    >
                      <div className="flex items-start gap-2">
                        {!n.read && <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: "#F5D547" }} />}
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-semibold truncate" style={{ color: "#1A1A1A" }}>{n.subject}</div>
                          <div className="text-xs mt-0.5 line-clamp-2 leading-relaxed text-gray-400">{n.body}</div>
                          {n.metadata?.actioned_by_name && (
                            <div className="text-[10px] mt-1 text-gray-400">
                              {n.metadata.status === "APPROVED" ? "✓ Approved" : "✗ Rejected"} by{" "}
                              <span className="font-semibold text-gray-600">{String(n.metadata.actioned_by_name)}</span>
                            </div>
                          )}
                          <div className="text-[10px] text-gray-300 mt-1">{new Date(n.created_at).toLocaleString("en-IN")}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Settings */}
        <button className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors text-gray-500">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" strokeWidth="2"/></svg>
        </button>

        {/* User avatar */}
        <button
          onClick={onLogout}
          className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all hover:opacity-80"
          style={{ background: "#F5D547", color: "#1A1A1A" }}
          title="Logout"
        >
          {initials}
        </button>
      </div>
    </header>
  );
}
