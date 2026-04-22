import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./LoginPage";
import AppShell from "./components/layout/AppShell";
import { isLoggedIn } from "./auth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  return isLoggedIn() ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        />
        {/* Legacy /chat route still works */}
        <Route
          path="/chat"
          element={<Navigate to="/dashboard" replace />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
