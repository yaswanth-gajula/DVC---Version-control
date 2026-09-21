import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE });

export const api = {
  listProjects: () => client.get("/api/projects").then((r) => r.data),

  createProject: (name) => client.post("/api/projects", { name }).then((r) => r.data),

  deleteProject: (projectId) => client.delete(`/api/projects/${projectId}`).then((r) => r.data),

  listVersions: (projectId) =>
    client.get(`/api/projects/${projectId}/versions`).then((r) => r.data),

  getVersion: (projectId, id) =>
    client.get(`/api/projects/${projectId}/versions/${id}`).then((r) => r.data),

  saveVersion: (projectId, files, message) => {
    const form = new FormData();
    form.append("message", message);
    files.forEach((f) => form.append("files", f, f.webkitRelativePath || f.name));
    return client
      .post(`/api/projects/${projectId}/versions`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },

  downloadVersion: (projectId, id) =>
    client
      .get(`/api/projects/${projectId}/versions/${id}/download`, { responseType: "blob" })
      .then((r) => r.data),

  downloadVersionDedup: (projectId, id) =>
    client
      .get(`/api/projects/${projectId}/versions/${id}/download-dedup`, { responseType: "blob" })
      .then((r) => r.data),

  storageGrowth: (projectId) =>
    client.get(`/api/projects/${projectId}/stats/storage-growth`).then((r) => r.data),

  dedupGrowth: (projectId) =>
    client.get(`/api/projects/${projectId}/stats/dedup-growth`).then((r) => r.data),

  diff: (projectId, fromVersion, toVersion) =>
    client
      .get(`/api/projects/${projectId}/diff`, {
        params: { from_version: fromVersion, to_version: toVersion },
      })
      .then((r) => r.data),

  gitLog: (projectId) => client.get(`/api/projects/${projectId}/git-log`).then((r) => r.data),
};

export function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
