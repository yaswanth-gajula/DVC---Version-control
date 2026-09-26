import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import BrandMark from "./BrandMark";

export default function Header({ projectName }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <header className="border-b border-border bg-surface">
      <div className="max-w-6xl mx-auto px-6 py-5 flex items-baseline justify-between">
        <div>
          <h1 className="brand-lockup text-lg font-semibold tracking-tight">
            <BrandMark />
            {projectName || "DVC Atlas"}{" "}
            <span className="text-muted font-normal">/ workspace</span>
          </h1>
          <p className="text-sm text-muted mt-0.5">
            Naive full-copy baseline — every save is a complete snapshot, tracked with real Git commits.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {user && <span className="text-xs text-muted">{user.email}</span>}
          <Link
            to="/projects"
            className="font-mono text-xs text-muted border border-border rounded px-2 py-1 hover:bg-bg transition-colors"
          >
            All projects
          </Link>
          <button
            onClick={handleSignOut}
            className="font-mono text-xs text-muted border border-border rounded px-2 py-1 hover:bg-bg transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}