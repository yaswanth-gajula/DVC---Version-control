import { formatDate } from "../api";

export default function GitLog({ commits }) {
  return (
    <div className="border border-border bg-surface rounded-md">
      <div className="px-4 py-3 border-b border-border flex items-baseline justify-between">
        <h2 className="text-sm font-medium">Git log</h2>
        <span className="text-xs text-muted">working tree</span>
      </div>
      {commits.length === 0 ? (
        <p className="text-sm text-muted px-4 py-6 text-center">No commits yet.</p>
      ) : (
        <ul className="divide-y divide-border max-h-64 overflow-y-auto">
          {commits.map((c) => (
            <li key={c.hash} className="px-4 py-2.5 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-accent">{c.hash}</span>
                <span className="truncate">{c.message}</span>
              </div>
              <span className="text-xs text-muted">{formatDate(c.date)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
