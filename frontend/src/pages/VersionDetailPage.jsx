import { useEffect, useState } from "react";
import { useParams, Link, useOutletContext } from "react-router-dom";
import { api, formatBytes, formatDate } from "../api";
import DiffView from "../components/DiffView";

const STATUS_DOT = {
  added: "bg-added",
  modified: "bg-accent",
  removed: "bg-removed",
  unchanged: "bg-border",
};

export default function VersionDetailPage() {
  const { id } = useParams();
  const { projectId } = useOutletContext();
  const versionId = Number(id);
  const [detail, setDetail] = useState(null);
  const [diff, setDiff] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setDetail(null);
    setDiff(null);
    setError(null);

    api.getVersion(projectId, versionId).then(setDetail).catch(() => setError("Version not found."));

    if (versionId > 1) {
      api.diff(projectId, versionId - 1, versionId).then(setDiff).catch(() => {});
    }
  }, [projectId, versionId]);

  const statusByPath = {};
  if (diff) {
    diff.files.forEach((f) => {
      if (f.status !== "removed") statusByPath[f.path] = f.status;
    });
  }

  async function handleDownload() {
    const blob = await api.downloadVersion(projectId, versionId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `version-${versionId}.zip`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  if (error) {
    return (
      <div className="text-sm text-muted">
        {error} <Link to={`/p/${projectId}/history`} className="text-accent hover:underline">Back to history</Link>
      </div>
    );
  }

  if (!detail) {
    return <p className="text-sm text-muted">Loading…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-base font-semibold">
            v{detail.id} <span className="font-normal text-muted">— {detail.message}</span>
          </h1>
          <p className="text-xs text-muted font-mono mt-0.5">
            {detail.commit_hash.slice(0, 10)} · {formatDate(detail.created_at)} · {detail.file_count} files · {formatBytes(detail.total_size_bytes)}
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="text-xs font-mono border border-border rounded px-2 py-1.5 hover:bg-bg transition-colors shrink-0"
        >
          Download .zip
        </button>
      </div>

      <div className="border border-border bg-surface rounded-md">
        <div className="px-4 py-2.5 border-b border-border text-sm font-medium flex items-center justify-between">
          <span>Files in this version</span>
          {versionId > 1 && (
            <span className="text-xs text-muted font-normal flex items-center gap-3">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-added inline-block" /> added</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-accent inline-block" /> modified</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-border inline-block" /> unchanged</span>
            </span>
          )}
        </div>
        <ul className="divide-y divide-border max-h-56 overflow-y-auto">
          {detail.files.map((f) => {
            const status = statusByPath[f.path];
            return (
              <li key={f.path} className="px-4 py-2 flex items-center gap-2 text-sm font-mono">
                {versionId > 1 && (
                  <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_DOT[status] || STATUS_DOT.unchanged}`} title={status || "unchanged"} />
                )}
                <span className="truncate flex-1">{f.path}</span>
                <span className="text-muted shrink-0 ml-3">{formatBytes(f.size_bytes)}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {versionId > 1 ? (
        diff && <DiffView diff={diff} />
      ) : (
        <p className="text-sm text-muted">First version — no prior version to diff against.</p>
      )}
    </div>
  );
}
