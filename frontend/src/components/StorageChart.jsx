import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { formatBytes } from "../api";

export default function StorageChart({ naiveData, dedupData }) {
  // Merge by version number so both lines share one x-axis, even if one
  // series is momentarily behind the other (e.g. right after a save).
  const byVersion = {};
  naiveData.forEach((d) => {
    byVersion[d.version] = { ...byVersion[d.version], version: d.version, naive: d.cumulative_naive_bytes };
  });
  dedupData.forEach((d) => {
    byVersion[d.version] = { ...byVersion[d.version], version: d.version, dedup: d.cumulative_dedup_bytes };
  });
  const chartData = Object.values(byVersion)
    .sort((a, b) => a.version - b.version)
    .map((d) => ({ ...d, label: `v${d.version}` }));

  const latest = chartData[chartData.length - 1];
  const savingsPct =
    latest && latest.naive > 0 ? Math.round((1 - latest.dedup / latest.naive) * 100) : null;

  return (
    <div className="border border-border bg-surface rounded-md p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-medium">Cumulative storage vs. version count</h2>
        {savingsPct !== null && (
          <span className="text-xs font-mono text-accent">
            {savingsPct >= 0 ? `${savingsPct}% less than naive` : "no savings yet"}
          </span>
        )}
      </div>
      {chartData.length === 0 ? (
        <p className="text-sm text-muted py-10 text-center">Save a version to see storage growth.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E4E4E1" />
            <XAxis dataKey="label" tick={{ fontSize: 12, fontFamily: "IBM Plex Mono" }} stroke="#6B7280" />
            <YAxis
              tick={{ fontSize: 12, fontFamily: "IBM Plex Mono" }}
              stroke="#6B7280"
              tickFormatter={(v) => formatBytes(v)}
              width={70}
            />
            <Tooltip
              formatter={(value, name) => [formatBytes(value), name]}
              contentStyle={{ fontFamily: "IBM Plex Mono", fontSize: 12, borderRadius: 6, borderColor: "#E4E4E1" }}
            />
            <Legend
              wrapperStyle={{ fontSize: 12, fontFamily: "IBM Plex Mono" }}
              formatter={(value) => (value === "naive" ? "Naive (O2 baseline)" : "Content-addressed (O3)")}
            />
            <Line type="monotone" dataKey="naive" stroke="#C5221F" strokeWidth={2} dot={{ r: 3 }} connectNulls />
            <Line type="monotone" dataKey="dedup" stroke="#0F6E64" strokeWidth={2} dot={{ r: 3 }} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
