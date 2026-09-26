"""
Local-disk versioning engine, scoped per user.

Per the explicit scope for this feature: Supabase is used ONLY for
authentication (login/signup, session tokens). Every user identified by
`user_id` here is a Supabase Auth user id (verified in auth.py), but all
project, version, and chunk DATA lives on local disk -- Supabase never
sees it, exactly as before this feature was added, just now partitioned
per user instead of shared globally.

Layout on disk:
  data/
    users/
      <user_id>/
        projects.json                  <- this user's project registry
        projects/
          <project_id>/
            working/                    <- real Git repo for this project
            versions/v1, v2, ...         <- O2: full-copy snapshots
            manifest.json                <- O2 metadata
            chunk_store/xx/<hash>        <- O3: content-addressed chunks
            dedup_manifest.json          <- O3 metadata
"""
import json
import os
import re
import shutil
import difflib
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from git import Repo, Actor

from .chunking import chunk_content

BASE_DIR = Path(__file__).parent.parent / "data"
USERS_DIR = BASE_DIR / "users"

GIT_AUTHOR = Actor("DVC Capstone Prototype", "prototype@dvc-capstone.local")


# ---------------------------------------------------------------------------
# Per-user, per-project path helpers
# ---------------------------------------------------------------------------

def _user_dir(user_id: str) -> Path:
    return USERS_DIR / user_id


def _projects_registry_path(user_id: str) -> Path:
    return _user_dir(user_id) / "projects.json"


def _projects_dir(user_id: str) -> Path:
    return _user_dir(user_id) / "projects"


def _project_dir(user_id: str, project_id: str) -> Path:
    return _projects_dir(user_id) / project_id


def _working_dir(user_id: str, project_id: str) -> Path:
    return _project_dir(user_id, project_id) / "working"


def _versions_dir(user_id: str, project_id: str) -> Path:
    return _project_dir(user_id, project_id) / "versions"


def _manifest_path(user_id: str, project_id: str) -> Path:
    return _project_dir(user_id, project_id) / "manifest.json"


def _chunk_store_dir(user_id: str, project_id: str) -> Path:
    return _project_dir(user_id, project_id) / "chunk_store"


def _dedup_manifest_path(user_id: str, project_id: str) -> Path:
    return _project_dir(user_id, project_id) / "dedup_manifest.json"


def _chunk_path(user_id: str, project_id: str, chunk_hash: str) -> Path:
    return _chunk_store_dir(user_id, project_id) / chunk_hash[:2] / chunk_hash


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


# ---------------------------------------------------------------------------
# Project registry (per user)
# ---------------------------------------------------------------------------

def _load_registry(user_id: str) -> List[Dict]:
    path = _projects_registry_path(user_id)
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_registry(user_id: str, registry: List[Dict]) -> None:
    _user_dir(user_id).mkdir(parents=True, exist_ok=True)
    with open(_projects_registry_path(user_id), "w") as f:
        json.dump(registry, f, indent=2)


def list_projects(user_id: str) -> List[Dict]:
    registry = _load_registry(user_id)
    for p in registry:
        manifest_path = _manifest_path(user_id, p["id"])
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            p["version_count"] = len(manifest)
            p["total_bytes"] = manifest[-1]["cumulative_naive_bytes"] if manifest else 0
        else:
            p["version_count"] = 0
            p["total_bytes"] = 0

        dedup_manifest_path = _dedup_manifest_path(user_id, p["id"])
        if dedup_manifest_path.exists():
            with open(dedup_manifest_path) as f:
                dedup_manifest = json.load(f)
            p["total_dedup_bytes"] = dedup_manifest[-1]["cumulative_dedup_bytes"] if dedup_manifest else 0
        else:
            p["total_dedup_bytes"] = 0
    return registry


def create_project(user_id: str, name: str) -> Dict:
    name = name.strip()
    if not name:
        raise ValueError("Project name cannot be empty")

    registry = _load_registry(user_id)
    base_slug = _slugify(name)
    slug = base_slug
    existing_ids = {p["id"] for p in registry}
    n = 2
    while slug in existing_ids:
        slug = f"{base_slug}-{n}"
        n += 1

    entry = {
        "id": slug,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    registry.append(entry)
    _save_registry(user_id, registry)

    _working_dir(user_id, slug).mkdir(parents=True, exist_ok=True)
    _versions_dir(user_id, slug).mkdir(parents=True, exist_ok=True)
    _ensure_repo(user_id, slug)
    _save_manifest(user_id, slug, [])

    return {**entry, "version_count": 0, "total_bytes": 0, "total_dedup_bytes": 0}


def delete_project(user_id: str, project_id: str) -> None:
    registry = _load_registry(user_id)
    new_registry = [p for p in registry if p["id"] != project_id]
    if len(new_registry) == len(registry):
        raise KeyError(f"project {project_id} not found")
    _save_registry(user_id, new_registry)
    project_dir = _project_dir(user_id, project_id)
    if project_dir.exists():
        shutil.rmtree(project_dir)


def _assert_project_exists(user_id: str, project_id: str) -> None:
    if not any(p["id"] == project_id for p in _load_registry(user_id)):
        raise KeyError(f"project {project_id} not found")


# ---------------------------------------------------------------------------
# Git + naive snapshot helpers
# ---------------------------------------------------------------------------

def _ensure_dirs(user_id: str, project_id: str) -> None:
    _working_dir(user_id, project_id).mkdir(parents=True, exist_ok=True)
    _versions_dir(user_id, project_id).mkdir(parents=True, exist_ok=True)


def _ensure_repo(user_id: str, project_id: str) -> Repo:
    _ensure_dirs(user_id, project_id)
    working = _working_dir(user_id, project_id)
    if not (working / ".git").exists():
        repo = Repo.init(working)
        repo.index.commit("Initialize repository", author=GIT_AUTHOR, committer=GIT_AUTHOR)
    else:
        repo = Repo(working)
    return repo


def _load_manifest(user_id: str, project_id: str) -> List[Dict]:
    path = _manifest_path(user_id, project_id)
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_manifest(user_id: str, project_id: str, manifest: List[Dict]) -> None:
    with open(_manifest_path(user_id, project_id), "w") as f:
        json.dump(manifest, f, indent=2)


def _load_dedup_manifest(user_id: str, project_id: str) -> List[Dict]:
    path = _dedup_manifest_path(user_id, project_id)
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_dedup_manifest(user_id: str, project_id: str, manifest: List[Dict]) -> None:
    with open(_dedup_manifest_path(user_id, project_id), "w") as f:
        json.dump(manifest, f, indent=2)


def _write_chunk_if_new(user_id: str, project_id: str, chunk_bytes: bytes) -> tuple[str, int]:
    chunk_hash = hashlib.sha256(chunk_bytes).hexdigest()
    path = _chunk_path(user_id, project_id, chunk_hash)
    if path.exists():
        return chunk_hash, 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(chunk_bytes)
    return chunk_hash, len(chunk_bytes)


def _dir_size_bytes(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            total += (Path(root) / name).stat().st_size
    return total


def _list_files(path: Path) -> List[Dict]:
    entries = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            rel = fp.relative_to(path).as_posix()
            entries.append({"path": rel, "size_bytes": fp.stat().st_size})
    return sorted(entries, key=lambda e: e["path"])


# ---------------------------------------------------------------------------
# Versioning operations
# ---------------------------------------------------------------------------

def save_version(user_id: str, project_id: str, uploaded_files: Dict[str, bytes], message: str) -> Dict:
    _assert_project_exists(user_id, project_id)
    _ensure_dirs(user_id, project_id)
    repo = _ensure_repo(user_id, project_id)
    working = _working_dir(user_id, project_id)
    versions_dir = _versions_dir(user_id, project_id)

    for item in working.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    for rel_path, content in uploaded_files.items():
        dest = working / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(content)

    repo.git.add(A=True)
    commit_message = message.strip() or "Unnamed version"
    if repo.is_dirty(untracked_files=True) or not repo.head.is_valid():
        commit = repo.index.commit(commit_message, author=GIT_AUTHOR, committer=GIT_AUTHOR)
        commit_hash = commit.hexsha
    else:
        commit_hash = repo.head.commit.hexsha

    manifest = _load_manifest(user_id, project_id)
    version_id = len(manifest) + 1

    # --- O2: naive full-copy baseline ---
    snapshot_dir = versions_dir / f"v{version_id}"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(working, snapshot_dir, ignore=shutil.ignore_patterns(".git"))

    total_size = _dir_size_bytes(snapshot_dir)
    file_count = sum(len(files) for _, _, files in os.walk(snapshot_dir))
    cumulative = (manifest[-1]["cumulative_naive_bytes"] if manifest else 0) + total_size

    entry = {
        "id": version_id,
        "message": commit_message,
        "commit_hash": commit_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": file_count,
        "total_size_bytes": total_size,
        "cumulative_naive_bytes": cumulative,
    }
    manifest.append(entry)
    _save_manifest(user_id, project_id, manifest)

    # --- O3: content-addressed, deduplicated storage ---
    dedup_files = {}
    new_bytes_written = 0
    for rel_path, content in uploaded_files.items():
        chunk_hashes = []
        for chunk in chunk_content(content):
            chunk_hash, written = _write_chunk_if_new(user_id, project_id, chunk)
            chunk_hashes.append(chunk_hash)
            new_bytes_written += written
        dedup_files[rel_path] = {"chunk_hashes": chunk_hashes, "size_bytes": len(content)}

    dedup_manifest = _load_dedup_manifest(user_id, project_id)
    cumulative_dedup_bytes = _dir_size_bytes(_chunk_store_dir(user_id, project_id))

    dedup_entry = {
        "id": version_id,
        "message": commit_message,
        "commit_hash": commit_hash,
        "created_at": entry["created_at"],
        "file_count": file_count,
        "total_logical_bytes": total_size,
        "new_bytes_written": new_bytes_written,
        "cumulative_dedup_bytes": cumulative_dedup_bytes,
        "files": dedup_files,
    }
    dedup_manifest.append(dedup_entry)
    _save_dedup_manifest(user_id, project_id, dedup_manifest)

    return entry


def list_versions(user_id: str, project_id: str) -> List[Dict]:
    _assert_project_exists(user_id, project_id)
    return _load_manifest(user_id, project_id)


def get_version(user_id: str, project_id: str, version_id: int) -> Dict:
    for entry in _load_manifest(user_id, project_id):
        if entry["id"] == version_id:
            files = _list_files(_versions_dir(user_id, project_id) / f"v{version_id}")
            return {**entry, "files": files}
    raise KeyError(f"version {version_id} not found")


def get_version_dir(user_id: str, project_id: str, version_id: int) -> Path:
    snapshot_dir = _versions_dir(user_id, project_id) / f"v{version_id}"
    if not snapshot_dir.exists():
        raise KeyError(f"version {version_id} not found")
    return snapshot_dir


def download_naive_zip(user_id: str, project_id: str, version_id: int) -> Path:
    return get_version_dir(user_id, project_id, version_id)


def storage_growth(user_id: str, project_id: str) -> List[Dict]:
    _assert_project_exists(user_id, project_id)
    return [
        {"version": e["id"], "cumulative_naive_bytes": e["cumulative_naive_bytes"]}
        for e in _load_manifest(user_id, project_id)
    ]


def dedup_storage_growth(user_id: str, project_id: str) -> List[Dict]:
    _assert_project_exists(user_id, project_id)
    return [
        {"version": e["id"], "cumulative_dedup_bytes": e["cumulative_dedup_bytes"]}
        for e in _load_dedup_manifest(user_id, project_id)
    ]


def get_dedup_version(user_id: str, project_id: str, version_id: int) -> Dict:
    for entry in _load_dedup_manifest(user_id, project_id):
        if entry["id"] == version_id:
            return entry
    raise KeyError(f"dedup version {version_id} not found")


def reconstruct_version_files(user_id: str, project_id: str, version_id: int) -> Dict[str, bytes]:
    entry = get_dedup_version(user_id, project_id, version_id)
    result = {}
    for rel_path, file_info in entry["files"].items():
        pieces = []
        for chunk_hash in file_info["chunk_hashes"]:
            path = _chunk_path(user_id, project_id, chunk_hash)
            with open(path, "rb") as f:
                pieces.append(f.read())
        result[rel_path] = b"".join(pieces)
    return result


def _read_text_safe(path: Path) -> List[str] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except (UnicodeDecodeError, FileNotFoundError):
        return None


def diff_versions(user_id: str, project_id: str, from_id: int, to_id: int) -> List[Dict]:
    from_dir = get_version_dir(user_id, project_id, from_id)
    to_dir = get_version_dir(user_id, project_id, to_id)

    from_files = {e["path"] for e in _list_files(from_dir)}
    to_files = {e["path"] for e in _list_files(to_dir)}

    results = []
    for path in sorted(from_files | to_files):
        in_from, in_to = path in from_files, path in to_files
        if in_from and not in_to:
            results.append({"path": path, "status": "removed", "diff": None})
        elif in_to and not in_from:
            results.append({"path": path, "status": "added", "diff": None})
        else:
            old_lines = _read_text_safe(from_dir / path)
            new_lines = _read_text_safe(to_dir / path)
            if old_lines is None or new_lines is None:
                same = (from_dir / path).stat().st_size == (to_dir / path).stat().st_size
                results.append({"path": path, "status": "unchanged" if same else "modified", "diff": None})
                continue
            if old_lines == new_lines:
                results.append({"path": path, "status": "unchanged", "diff": None})
            else:
                diff_text = "".join(
                    difflib.unified_diff(old_lines, new_lines, fromfile=f"v{from_id}/{path}", tofile=f"v{to_id}/{path}")
                )
                results.append({"path": path, "status": "modified", "diff": diff_text})
    return results


def git_log(user_id: str, project_id: str) -> List[Dict]:
    _assert_project_exists(user_id, project_id)
    repo = _ensure_repo(user_id, project_id)
    entries = []
    for commit in repo.iter_commits():
        entries.append({
            "hash": commit.hexsha[:10],
            "message": commit.message.strip(),
            "author": commit.author.name,
            "date": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat(),
        })
    return entries