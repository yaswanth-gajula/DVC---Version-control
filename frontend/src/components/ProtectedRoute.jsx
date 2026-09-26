import { Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import PageBackdrop from "./PageBackdrop";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center relative">
        <PageBackdrop variant="auth" />
        <p className="text-sm text-muted">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}