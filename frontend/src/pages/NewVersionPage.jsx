import { useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPanel from "../components/UploadPanel";
import { api } from "../api";

export default function NewVersionPage() {
  const { projectId, refresh } = useOutletContext();
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  async function handleSave(files, message) {
    setSaving(true);
    try {
      const result = await api.saveVersion(projectId, files, message);
      await refresh();
      navigate(`/p/${projectId}/history/${result.version.id}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 max-w-xl">
      <div>
        <h1 className="text-base font-semibold">New version</h1>
        <p className="text-sm text-muted mt-0.5">
          Select the files or folder representing this version's complete state. The full set replaces the previous working tree — deletions are captured too.
        </p>
      </div>
      <UploadPanel onSave={handleSave} saving={saving} />
    </div>
  );
}
