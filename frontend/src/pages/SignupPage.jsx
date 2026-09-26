import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import PageBackdrop from "../components/PageBackdrop";
import BrandMark from "../components/BrandMark";

export default function SignupPage() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const { data, error } = await signUp(email, password);
    setSubmitting(false);
    if (error) {
      setError(error.message);
      return;
    }
    // If email confirmation is required, Supabase returns a user but no
    // active session yet. If confirmation is disabled in your project
    // settings, session is set immediately and we can go straight in.
    if (data.session) {
      navigate("/projects", { replace: true });
    } else {
      setNeedsConfirmation(true);
    }
  }

  if (needsConfirmation) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center px-6 relative">
        <PageBackdrop variant="auth" />
        <div className="w-full max-w-sm text-center">
          <h1 className="text-xl font-semibold">Check your email</h1>
          <p className="text-sm text-muted mt-2">
            We sent a confirmation link to <span className="text-ink">{email}</span>. Confirm your
            address, then sign in.
          </p>
          <Link to="/login" className="inline-block mt-4 text-accent text-sm hover:underline">
            Back to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-6 relative">
      <PageBackdrop variant="auth" />
      <div className="w-full max-w-sm">
        <Link to="/" className="brand-lockup text-lg font-semibold tracking-tight">
          <BrandMark />
          DVC Atlas
        </Link>
        <h1 className="text-xl font-semibold mt-6">Create an account</h1>
        <p className="text-sm text-muted mt-1">Start tracking your projects.</p>

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
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-sm border border-border rounded px-3 py-2 bg-surface focus:outline-none focus:ring-2 focus:ring-accent/40"
            />
            <p className="text-xs text-muted mt-1">At least 6 characters.</p>
          </div>

          {error && <p className="text-sm text-removed">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full text-sm font-medium bg-accent text-white rounded px-3 py-2 disabled:opacity-40 hover:bg-accent/90 transition-colors"
          >
            {submitting ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="text-sm text-muted mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}