import { Link } from "react-router-dom";

export default function Header({ projectName }) {
  return (
    <header className="border-b border-border bg-surface">
      <div className="max-w-6xl mx-auto px-6 py-5 flex items-baseline justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            {projectName || "Version Store"}{" "}
            <span className="text-muted font-normal">/ CP1 prototype</span>
          </h1>
          <p className="text-sm text-muted mt-0.5">
            Naive full-copy baseline — every save is a complete snapshot, tracked with real Git commits.
          </p>
        </div>
        <Link
          to="/"
          className="font-mono text-xs text-muted border border-border rounded px-2 py-1 hover:bg-bg transition-colors"
        >
          All projects
        </Link>
      </div>
    </header>
  );
}
