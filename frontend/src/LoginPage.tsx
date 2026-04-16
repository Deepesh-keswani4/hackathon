import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "./api";
import { saveTokens } from "./auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await login(email, password);
      saveTokens(tokens.access, tokens.refresh);
      navigate("/chat");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex"
      style={{ background: "#FBF4ED" }}
    >
      {/* Left panel — brand */}
      <div
        className="hidden lg:flex flex-col justify-between w-1/2 px-16 py-12"
        style={{ background: "#1C0F07" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
            style={{ background: "#E8622A" }}
          >
            HE
          </div>
          <span className="text-white text-base font-semibold tracking-tight">Human Edge</span>
        </div>

        {/* Hero copy */}
        <div>
          <div
            className="inline-block text-xs font-semibold px-3 py-1 rounded-full mb-6"
            style={{ background: "rgba(232,98,42,0.15)", color: "#E8622A" }}
          >
            AI-ENABLED HRMS
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-4" style={{ color: "#FBF4ED" }}>
            Build high-performance teams with people insights that actually predict outcomes.
          </h1>
          <p className="text-sm leading-relaxed" style={{ color: "#8B6147" }}>
            Human Edge combines workforce analytics, engagement intelligence, and retention forecasting into one actionable command center.
          </p>

          <ul className="mt-8 space-y-2">
            {[
              "Predict attrition risks before they escalate",
              "Track productivity trends across departments",
              "Turn HR reports into weekly decisions",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2 text-sm" style={{ color: "#C4A99A" }}>
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: "#E8622A" }}
                />
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Bottom stats */}
        <div className="flex gap-8">
          {[
            { value: "1,248", label: "Active employees" },
            { value: "4.6", label: "Avg manager rating" },
            { value: "94", label: "Leave requests/week" },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-xl font-bold" style={{ color: "#FBF4ED" }}>{stat.value}</p>
              <p className="text-xs mt-0.5" style={{ color: "#6B4F3A" }}>{stat.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-col flex-1 items-center justify-center px-8 py-12">
        {/* Mobile logo */}
        <div className="flex items-center gap-2 mb-10 lg:hidden">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
            style={{ background: "#E8622A" }}
          >
            HE
          </div>
          <span className="text-base font-semibold" style={{ color: "#1C0F07" }}>Human Edge</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-1" style={{ color: "#1C0F07" }}>
              Welcome back
            </h2>
            <p className="text-sm" style={{ color: "#8B6147" }}>
              Sign in to your Human Edge account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                className="block text-xs font-semibold mb-1.5 uppercase tracking-wide"
                style={{ color: "#6B4F3A" }}
              >
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E8D9CC",
                  color: "#1C0F07",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = "#E8622A")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "#E8D9CC")}
              />
            </div>

            <div>
              <label
                className="block text-xs font-semibold mb-1.5 uppercase tracking-wide"
                style={{ color: "#6B4F3A" }}
              >
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E8D9CC",
                  color: "#1C0F07",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = "#E8622A")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "#E8D9CC")}
              />
            </div>

            {error && (
              <div
                className="text-sm rounded-xl px-4 py-3"
                style={{
                  background: "#FEF2F2",
                  border: "1px solid #FCA5A5",
                  color: "#991B1B",
                }}
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full font-semibold py-3 rounded-xl text-sm transition-all disabled:opacity-60"
              style={{ background: "#E8622A", color: "#FFFFFF" }}
              onMouseEnter={(e) => {
                if (!loading)
                  (e.currentTarget as HTMLButtonElement).style.background = "#C94E1E";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "#E8622A";
              }}
            >
              {loading ? "Signing in…" : "Login to Human Edge"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
