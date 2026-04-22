import React, { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "./api";
import { saveTokens } from "./auth";

const FEATURES = [
  { label: "Smart Leave", desc: "AI-powered approvals" },
  { label: "Attendance", desc: "Auto-regularization" },
  { label: "AI Assistant", desc: "Chat with HR data" },
  { label: "Analytics", desc: "People insights" },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await login(email, password);
      saveTokens(tokens.access, tokens.refresh);
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: "#EDECEA" }}>

      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-[55%] px-16 py-12">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-[#111111] flex items-center justify-center text-white font-bold text-sm">H</div>
          <div>
            <div className="font-bold text-[#111111] text-sm">HRMS</div>
            <div className="text-[10px] text-gray-400">AI-Powered</div>
          </div>
        </div>

        {/* Hero */}
        <div className="space-y-10">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E8D44D]/40 text-xs font-semibold text-[#111111]/70 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#111111]" />
              AI-Enabled HR Platform
            </div>
            <h1 className="text-5xl font-bold text-[#111111] leading-[1.1] tracking-tight">
              The smartest<br />HR workspace<br />
              <span style={{ color: "#E8D44D", WebkitTextStroke: "1px #111111" }}>you'll ever use.</span>
            </h1>
            <p className="text-gray-500 mt-5 text-base leading-relaxed max-w-sm">
              Leave management, attendance, org insights — powered by conversational AI. No forms, no friction.
            </p>
          </div>

          {/* Feature grid */}
          <div className="grid grid-cols-2 gap-3">
            {FEATURES.map((f, i) => (
              <div
                key={f.label}
                className={`p-4 rounded-2xl shadow-[0_1px_4px_rgba(0,0,0,0.07)] ${i === 0 ? "bg-[#111111]" : i === 1 ? "bg-[#E8D44D]" : "bg-white"}`}
              >
                <div className={`text-sm font-bold mb-0.5 ${i === 0 ? "text-white" : "text-[#111111]"}`}>{f.label}</div>
                <div className={`text-xs ${i === 0 ? "text-white/50" : "text-gray-500"}`}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-10">
          {[
            { val: "+18K", label: "Requests processed" },
            { val: "94%", label: "AI accuracy" },
            { val: "4.8★", label: "Satisfaction" },
          ].map(s => (
            <div key={s.label}>
              <div className="text-2xl font-bold text-[#111111]">{s.val}</div>
              <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-col flex-1 items-center justify-center px-8 py-12">
        {/* Mobile logo */}
        <div className="flex items-center gap-2 mb-10 lg:hidden">
          <div className="w-9 h-9 rounded-xl bg-[#111111] flex items-center justify-center text-white text-xs font-bold">H</div>
          <span className="font-bold text-[#111111] text-base">HRMS</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="bg-white rounded-3xl p-8 shadow-[0_4px_24px_rgba(0,0,0,0.08)]">
            <div className="mb-7">
              <div className="w-11 h-11 rounded-2xl bg-[#E8D44D] flex items-center justify-center mb-5">
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="#111" strokeWidth="2" strokeLinecap="round"/><circle cx="12" cy="7" r="4" stroke="#111" strokeWidth="2"/></svg>
              </div>
              <h2 className="text-2xl font-bold text-[#111111] tracking-tight">Welcome back</h2>
              <p className="text-sm text-gray-400 mt-1">Sign in to your workspace</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full px-4 py-3 rounded-xl text-sm text-gray-900 bg-gray-50 border border-gray-200 focus:outline-none focus:border-[#E8D44D] focus:bg-white transition-all placeholder-gray-300"
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPass ? "text" : "password"}
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl text-sm text-gray-900 bg-gray-50 border border-gray-200 focus:outline-none focus:border-[#E8D44D] focus:bg-white transition-all placeholder-gray-300 pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(v => !v)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors text-xs font-semibold"
                  >
                    {showPass ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {error && (
                <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-[#111111] text-white text-sm font-semibold hover:bg-gray-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in…
                  </>
                ) : (
                  <>Sign in →</>
                )}
              </button>
            </form>

            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px bg-gray-100" />
              <span className="text-[10px] text-gray-300 font-medium">SECURED</span>
              <div className="flex-1 h-px bg-gray-100" />
            </div>

            <div className="flex items-center justify-center gap-4">
              {["JWT Auth", "AES-256", "SOC2"].map(b => (
                <div key={b} className="flex items-center gap-1 text-[10px] text-gray-300 font-medium">
                  <span>✓</span>
                  <span>{b}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-center text-xs text-gray-400 mt-5">
            HRMS · AI-Powered Human Resource Management
          </p>
        </div>
      </div>
    </div>
  );
}
