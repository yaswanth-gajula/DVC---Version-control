import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, formatBytes, formatDate } from "../api";
import { useAuth } from "../AuthContext";
import PageBackdrop from "../components/PageBackdrop";
import BrandMark from "../components/BrandMark";

export default function ProjectsListPage() {
  const { user, signOut } = useAuth();
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  function refresh() {
    return api.listProjects().then(setProjects);
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const project = await api.createProject(name.trim());
      setName("");
      await refresh();
      navigate(`/p/${project.id}`);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Couldn't create the project. Check that the backend is running and reachable."
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(e, projectId) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this project and all its versions? This can't be undone.")) return;
    await api.deleteProject(projectId);
    refresh();
  }

  async function handleSignOut() {
    await signOut();
    navigate("/", { replace: true });
  }

  return (
    <div className="min-h-screen bg-bg relative">
      <PageBackdrop variant="projects" />
      <header className="border-b border-border bg-surface">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-baseline justify-between">
          <div>
            <h1 className="brand-lockup text-lg font-semibold tracking-tight"><BrandMark />DVC Atlas</h1>
            <p className="text-sm text-muted mt-0.5">
              Pick a project to work in, or start a new one. Every project has its own isolated version history.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {user && <span className="text-xs text-muted">{user.email}</span>}
            <button
              onClick={handleSignOut}
              className="font-mono text-xs text-muted border border-border rounded px-2 py-1 hover:bg-bg transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-6 space-y-4">
        <form onSubmit={handleCreate} className="border border-border bg-surface rounded-md p-4 flex gap-2">
          <input
            type="text"
            placeholder="New project name, e.g. Billing Service"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 text-sm border border-border rounded px-3 py-2 bg-bg focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
          <button
            type="submit"
            disabled={!name.trim() || creating}
            className="text-sm font-medium bg-accent text-white rounded px-4 py-2 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
          >
            {creating ? "Creating…" : "Create project"}
          </button>
        </form>

        {error && (
          <div className="border border-removed/30 bg-removed/5 text-removed text-sm rounded-md px-4 py-3">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : projects.length === 0 ? (
          <div className="border border-border bg-surface rounded-md p-8 text-center text-sm text-muted">
            No projects yet. Create your first one above.
          </div>
        ) : (
          <div className="border border-border bg-surface rounded-md">
            <ul className="divide-y divide-border">
              {projects.map((p) => (
                <li key={p.id}>
                  <Link
                    to={`/p/${p.id}`}
                    className="px-4 py-3 flex items-center gap-4 hover:bg-bg transition-colors"
                  >
                    <span className="flex-1 min-w-0">
                      <span className="block text-sm font-medium truncate">{p.name}</span>
                      <span className="block text-xs text-muted font-mono mt-0.5">
                        {p.version_count} version{p.version_count !== 1 ? "s" : ""} · {formatBytes(p.total_bytes)} · created {formatDate(p.created_at)}
                      </span>
                    </span>
                    <button
                      onClick={(e) => handleDelete(e, p.id)}
                      className="text-xs text-muted hover:text-removed shrink-0"
                    >
                      Delete
                    </button>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}