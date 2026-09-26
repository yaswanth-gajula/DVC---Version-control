import { useEffect, useState, useCallback } from "react";
import { BrowserRouter, Routes, Route, Outlet, useParams, Link } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import PageBackdrop from "./components/PageBackdrop";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import ProjectsListPage from "./pages/ProjectsListPage";
import OverviewPage from "./pages/OverviewPage";
import NewVersionPage from "./pages/NewVersionPage";
import HistoryPage from "./pages/HistoryPage";
import VersionDetailPage from "./pages/VersionDetailPage";
import GitLogPage from "./pages/GitLogPage";
import { api } from "./api";

function ProjectLayout() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [versions, setVersions] = useState([]);
  const [growth, setGrowth] = useState([]);
  const [dedupGrowth, setDedupGrowth] = useState([]);
  const [commits, setCommits] = useState([]);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [projects, v, g, dg, c] = await Promise.all([
        api.listProjects(),
        api.listVersions(projectId),
        api.storageGrowth(projectId),
        api.dedupGrowth(projectId),
        api.gitLog(projectId),
      ]);
      const current = projects.find((p) => p.id === projectId);
      setProject(current || null);
      setVersions(v);
      setGrowth(g);
      setDedupGrowth(dg);
      setCommits(c);
      setError(current ? null : "Project not found.");
    } catch (e) {
      setError("Can't reach the backend. Is it running on http://localhost:8000?");
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (error === "Project not found.") {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center relative">
        <PageBackdrop variant="project" />
        <div className="text-center">
          <p className="text-sm text-muted mb-2">{error}</p>
          <Link to="/projects" className="text-accent text-sm hover:underline">
            Back to all projects
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg relative">
      <PageBackdrop variant="project" />
      <Header projectName={project?.name} />
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row">
        <Sidebar projectId={projectId} />
        <main className="flex-1 py-6 pl-6 min-w-0">
          {error && (
            <div className="border border-removed/30 bg-removed/5 text-removed text-sm rounded-md px-4 py-3 mb-4">
              {error}
            </div>
          )}
          <Outlet context={{ projectId, versions, growth, dedupGrowth, commits, refresh }} />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/p/:projectId"
            element={
              <ProtectedRoute>
                <ProjectLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<OverviewPage />} />
            <Route path="new" element={<NewVersionPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="history/:id" element={<VersionDetailPage />} />
            <Route path="git-log" element={<GitLogPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}