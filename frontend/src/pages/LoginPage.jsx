import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../AuthContext";
import PageBackdrop from "../components/PageBackdrop";
import BrandMark from "../components/BrandMark";

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = location.state?.from || "/projects";

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const { error } = await signIn(email, password);
    setSubmitting(false);
    if (error) {
      setError(error.message);
      return;
    }
    navigate(redirectTo, { replace: true });
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-6 relative">
      <PageBackdrop variant="auth" />
      <div className="w-full max-w-sm">
        <Link to="/" className="brand-lockup text-lg font-semibold tracking-tight">
          <BrandMark />
          DVC Atlas
        </Link>
        <h1 className="text-xl font-semibold mt-6">Sign in</h1>
        <p className="text-sm text-muted mt-1">Welcome back.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <div>
            <label className="block text-xs text-muted mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full text-sm border border-border rounded px-3 py-2 bg-surface focus:outline-none focus:ring-2 focus:ring-accent/40"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-sm border border-border rounded px-3 py-2 bg-surface focus:outline-none focus:ring-2 focus:ring-accent/40"
            />
          </div>

          {error && <p className="text-sm text-removed">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full text-sm font-medium bg-accent text-white rounded px-3 py-2 disabled:opacity-40 hover:bg-accent/90 transition-colors"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-sm text-muted mt-4">
          Don't have an account?{" "}
          <Link to="/signup" className="text-accent hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}