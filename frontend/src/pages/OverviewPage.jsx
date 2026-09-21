import { useOutletContext } from "react-router-dom";
import StatsBar from "../components/StatsBar";
import StorageChart from "../components/StorageChart";

export default function OverviewPage() {
  const { versions, growth, dedupGrowth } = useOutletContext();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-base font-semibold">Overview</h1>
        <p className="text-sm text-muted mt-0.5">
          Naive full-copy storage (O2 baseline) versus content-addressed, deduplicated storage (O3 contribution) — same versions, same files, measured side by side.
        </p>
      </div>
      <StatsBar versions={versions} naiveGrowth={growth} dedupGrowth={dedupGrowth} />
      <StorageChart naiveData={growth} dedupData={dedupGrowth} />
    </div>
  );
}
