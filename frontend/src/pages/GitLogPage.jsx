import { useOutletContext } from "react-router-dom";
import GitLog from "../components/GitLog";

export default function GitLogPage() {
  const { commits } = useOutletContext();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-base font-semibold">Git log</h1>
        <p className="text-sm text-muted mt-0.5">
          Real commit history from the working tree — every saved version is a genuine Git commit, not a synthetic manifest entry.
        </p>
      </div>
      <GitLog commits={commits} />
    </div>
  );
}
