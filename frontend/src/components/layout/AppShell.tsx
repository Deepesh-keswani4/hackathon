import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { NavPage } from "./Sidebar";
import TopBar from "./TopBar";
import Dashboard from "../dashboard/Dashboard";
import LeavePage from "../leaves/LeavePage";
import AttendancePage from "../attendance/AttendancePage";
import EmployeePage from "../employees/EmployeePage";
import { getAccess, clearTokens, getValidToken } from "../../auth";
import { fetchMe, fetchUnreadNotifications, refreshToken, WS_BASE, UserProfile, NotificationItem } from "../../api";
import ChatPage from "../../ChatPage";

export default function AppShell() {
  const navigate = useNavigate();
  const [page, setPage] = useState<NavPage>("dashboard");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string>("");
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const seenIds = useRef<Set<number>>(new Set());

  useEffect(() => {
    async function init() {
      try {
        const t = await getValidToken(refreshToken);
        setToken(t);
        const me = await fetchMe(t);
        if (me) setProfile(me);
        const notifs = await fetchUnreadNotifications(t);
        setNotifications(notifs);
        const unread = notifs.filter(n => !n.read);
        unread.forEach(n => seenIds.current.add(n.id));
        setUnreadCount(unread.length);
        connectWS(t);
      } catch {
        handleLogout();
      }
    }
    init();
    return () => wsRef.current?.close();
  }, []);

  function connectWS(t: string) {
    const ws = new WebSocket(`${WS_BASE}/ws/notifications/?token=${t}`);
    wsRef.current = ws;
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === "notification") {
          if (!seenIds.current.has(data.id)) {
            seenIds.current.add(data.id);
            setNotifications(prev => [{
              id: data.id,
              subject: data.subject,
              body: data.body,
              metadata: data.metadata ?? {},
              read: false,
              created_at: data.created_at ?? new Date().toISOString(),
            }, ...prev]);
            setUnreadCount(c => c + 1);
          }
        }
      } catch {}
    };
    ws.onclose = () => {
      setTimeout(() => {
        const tk = getAccess();
        if (tk) connectWS(tk);
      }, 3000);
    };
  }

  function handleMarkRead(id: number) {
    const tk = getAccess();
    if (tk) {
      fetch(`${import.meta.env.VITE_API_BASE ?? "http://localhost:8002/api"}/notifications/${id}/mark_read/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${tk}` },
      }).catch(() => {});
    }
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    setUnreadCount(c => Math.max(0, c - 1));
  }

  function handleLogout() {
    clearTokens();
    navigate("/");
  }

  if (page === "chat") {
    return (
      <div className="flex flex-col h-screen" style={{ background: "#EEEADE" }}>
        <TopBar
          page={page}
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkRead={handleMarkRead}
          onNav={setPage}
          userName={profile?.name ?? ""}
          onLogout={handleLogout}
        />
        <div className="flex-1 min-h-0">
          <ChatPage embedded onNav={(p) => setPage(p as NavPage)} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "#EEEADE" }}>
      <TopBar
        page={page}
        notifications={notifications}
        unreadCount={unreadCount}
        onMarkRead={handleMarkRead}
        onNav={setPage}
        userName={profile?.name ?? ""}
        onLogout={handleLogout}
      />
      <main className="flex-1 overflow-y-auto">
        {token && (
          <>
            {page === "dashboard" && <Dashboard token={token} role={profile?.role ?? ""} userName={profile?.name ?? ""} onNav={setPage} />}
            {page === "leaves" && <LeavePage token={token} role={profile?.role ?? ""} />}
            {page === "attendance" && <AttendancePage token={token} role={profile?.role ?? ""} />}
            {page === "employees" && <EmployeePage token={token} role={profile?.role ?? ""} />}
          </>
        )}
      </main>
    </div>
  );
}
