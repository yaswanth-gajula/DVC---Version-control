import { useOutletContext } from "react-router-dom";
import VersionList from "../components/VersionList";

export default function HistoryPage() {
  const { versions } = useOutletContext();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-base font-semibold">Version history</h1>
        <p className="text-sm text-muted mt-0.5">Every saved version, newest first. Select one to view files, diff, or download.</p>
      </div>
      <VersionList versions={versions} />
    </div>
  );
}
