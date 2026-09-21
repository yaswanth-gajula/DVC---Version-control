const STATUS_STYLES = {
  added: "text-added",
  removed: "text-removed",
  modified: "text-accent",
  unchanged: "text-muted",
};

const STATUS_LABEL = {
  added: "added",
  removed: "removed",
  modified: "modified",
  unchanged: "unchanged",
};

function DiffLine({ line }) {
  if (line.startsWith("+") && !line.startsWith("+++")) {
    return <div className="bg-added/10 text-added px-2">{line}</div>;
  }
  if (line.startsWith("-") && !line.startsWith("---")) {
    return <div className="bg-removed/10 text-removed px-2">{line}</div>;
  }
  if (line.startsWith("@@")) {
    return <div className="text-accent px-2">{line}</div>;
  }
  return <div className="text-muted px-2">{line}</div>;
}

export default function DiffView({ diff }) {
  if (!diff) return null;
  const changed = diff.files.filter((f) => f.status !== "unchanged");

  return (
    <div className="mt-3 border border-border rounded-md">
      <div className="px-3 py-2 border-b border-border text-xs font-mono text-muted">
        v{diff.from_version} → v{diff.to_version} · {changed.length} file{changed.length !== 1 ? "s" : ""} changed
      </div>
      {changed.length === 0 ? (
        <p className="text-sm text-muted px-3 py-4">No differences between these versions.</p>
      ) : (
        <ul className="divide-y divide-border">
          {changed.map((f) => (
            <li key={f.path} className="p-3">
              <div className="flex items-center gap-2 text-sm font-mono">
                <span className={`text-xs uppercase tracking-wide ${STATUS_STYLES[f.status]}`}>
                  {STATUS_LABEL[f.status]}
                </span>
                <span>{f.path}</span>
              </div>
              {f.diff && (
                <pre className="mt-2 text-xs font-mono bg-bg border border-border rounded overflow-x-auto">
                  {f.diff.split("\n").map((line, i) => (
                    <DiffLine key={i} line={line} />
                  ))}
                </pre>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
