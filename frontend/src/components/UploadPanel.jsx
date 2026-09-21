import { useRef, useState, useEffect } from "react";

export default function UploadPanel({ onSave, saving }) {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  // webkitdirectory isn't a real JSX/HTML attribute -- React can silently
  // drop it if set as a string prop in some browsers, so set it imperatively
  // on the DOM node to guarantee the folder picker actually enables it.
  useEffect(() => {
    if (folderInputRef.current) {
      folderInputRef.current.webkitdirectory = true;
      folderInputRef.current.directory = true;
    }
  }, []);

  function addFiles(fileList) {
    setFiles((prev) => [...prev, ...Array.from(fileList)]);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  }

  function removeFile(idx) {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  }

  function handleSubmit() {
    if (!files.length || !message.trim()) return;
    onSave(files, message).then(() => {
      setFiles([]);
      setMessage("");
    });
  }

  const canSave = files.length > 0 && message.trim().length > 0 && !saving;

  return (
    <div className="border border-border bg-surface rounded-md p-4">
      <h2 className="text-sm font-medium mb-3">Save a new version</h2>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border border-dashed rounded-md px-4 py-6 text-center transition-colors ${
          dragActive ? "border-accent bg-accentSoft" : "border-border"
        }`}
      >
        <p className="text-sm text-muted mb-2">Drag files or a folder here</p>
        <div className="flex items-center justify-center gap-2 text-sm">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 border border-border rounded hover:bg-bg transition-colors"
          >
            Choose files
          </button>
          <button
            type="button"
            onClick={() => folderInputRef.current?.click()}
            className="px-3 py-1.5 border border-border rounded hover:bg-bg transition-colors"
          >
            Choose folder
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <input
          ref={folderInputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <ul className="mt-3 max-h-32 overflow-y-auto text-sm font-mono divide-y divide-border border border-border rounded">
          {files.map((f, i) => (
            <li key={i} className="flex items-center justify-between px-2 py-1">
              <span className="truncate">{f.webkitRelativePath || f.name}</span>
              <button
                onClick={() => removeFile(i)}
                className="text-muted hover:text-removed ml-2 shrink-0"
                aria-label={`Remove ${f.name}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <input
        type="text"
        placeholder="Version message, e.g. Add retry logic to sync worker"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        className="mt-3 w-full text-sm border border-border rounded px-3 py-2 bg-bg focus:outline-none focus:ring-2 focus:ring-accent/40"
      />

      <button
        onClick={handleSubmit}
        disabled={!canSave}
        className="mt-3 w-full text-sm font-medium bg-accent text-white rounded px-3 py-2 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent/90 transition-colors"
      >
        {saving ? "Saving version…" : "Save version"}
      </button>
    </div>
  );
}
