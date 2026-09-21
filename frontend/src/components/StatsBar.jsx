import { formatBytes } from "../api";

function Stat({ label, value, accent }) {
  return (
    <div className="border border-border bg-surface rounded-md px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-lg font-mono mt-1 ${accent ? "text-accent" : ""}`}>{value}</div>
    </div>
  );
}

export default function StatsBar({ versions, naiveGrowth, dedupGrowth }) {
  const count = versions.length;
  const naiveTotal = naiveGrowth.length > 0 ? naiveGrowth[naiveGrowth.length - 1].cumulative_naive_bytes : 0;
  const dedupTotal = dedupGrowth.length > 0 ? dedupGrowth[dedupGrowth.length - 1].cumulative_dedup_bytes : 0;
  const savingsPct = naiveTotal > 0 ? Math.round((1 - dedupTotal / naiveTotal) * 100) : 0;

  return (
    <div className="grid grid-cols-4 gap-3">
      <Stat label="Versions saved" value={count} />
      <Stat label="Naive storage (O2)" value={formatBytes(naiveTotal)} />
      <Stat label="Dedup storage (O3)" value={formatBytes(dedupTotal)} />
      <Stat label="Storage saved" value={count > 0 ? `${savingsPct}%` : "—"} accent />
    </div>
  );
}
