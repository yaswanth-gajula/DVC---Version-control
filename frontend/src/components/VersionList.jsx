import { Link, useOutletContext } from "react-router-dom";
import { formatBytes, formatDate } from "../api";

export default function VersionList({ versions }) {
  const { projectId } = useOutletContext();
  const sorted = [...versions].sort((a, b) => b.id - a.id);

  if (sorted.length === 0) {
    return (
      <div className="border border-border bg-surface rounded-md p-8 text-center text-sm text-muted">
        No versions saved yet.{" "}
        <Link to={`/p/${projectId}/new`} className="text-accent hover:underline">
          Save your first version
        </Link>
        .
      </div>
    );
  }

  return (
    <div className="border border-border bg-surface rounded-md">
      <ul className="divide-y divide-border">
        {sorted.map((v) => (
          <li key={v.id}>
            <Link
              to={`/p/${projectId}/history/${v.id}`}
              className="w-full text-left px-4 py-3 flex items-center gap-4 hover:bg-bg transition-colors"
            >
              <span className="font-mono text-xs text-muted w-8 shrink-0">v{v.id}</span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm truncate">{v.message}</span>
                <span className="block text-xs text-muted font-mono mt-0.5">
                  {v.commit_hash.slice(0, 10)} · {formatDate(v.created_at)}
                </span>
              </span>
              <span className="text-xs font-mono text-muted shrink-0">{v.file_count} files</span>
              <span className="text-xs font-mono shrink-0 w-16 text-right">{formatBytes(v.total_size_bytes)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
