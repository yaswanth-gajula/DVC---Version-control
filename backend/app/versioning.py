"""
CP1 versioning engine — now with multiple isolated PROJECTS.

Every project gets its own working tree, its own Git repo, its own
full-copy version snapshots, and its own manifest -- nothing is shared
between projects, so saving a version in "Project A" can never touch
"Project B"'s files or history.

Layout on disk:
  data/
    projects.json              <- registry: [{id, name, created_at}, ...]
    projects/
      <project_id>/
        working/                <- real Git repo for THIS project only
        versions/
          v1/, v2/, ...          <- full-copy snapshots for THIS project only
        manifest.json            <- version metadata for THIS project only
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

BASE_DIR = Path(__file__).parent / "data"
PROJECTS_DIR = BASE_DIR / "projects"
PROJECTS_REGISTRY_PATH = BASE_DIR / "projects.json"

GIT_AUTHOR = Actor("DVC Capstone Prototype", "prototype@dvc-capstone.local")


# ---------------------------------------------------------------------------
# Project registry
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


def _load_registry() -> List[Dict]:
    if not PROJECTS_REGISTRY_PATH.exists():
        return []
    with open(PROJECTS_REGISTRY_PATH, "r") as f:
        return json.load(f)


def _save_registry(registry: List[Dict]) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROJECTS_REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def list_projects() -> List[Dict]:
    registry = _load_registry()
    for p in registry:
        manifest_path = PROJECTS_DIR / p["id"] / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            p["version_count"] = len(manifest)
            p["total_bytes"] = manifest[-1]["cumulative_naive_bytes"] if manifest else 0
        else:
            p["version_count"] = 0
            p["total_bytes"] = 0
    return registry


def create_project(name: str) -> Dict:
    name = name.strip()
    if not name:
        raise ValueError("Project name cannot be empty")

    registry = _load_registry()
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
    _save_registry(registry)

    project_dir = PROJECTS_DIR / slug
    (project_dir / "working").mkdir(parents=True, exist_ok=True)
    (project_dir / "versions").mkdir(parents=True, exist_ok=True)
    _ensure_repo(slug)
    _save_manifest(slug, [])

    return {**entry, "version_count": 0, "total_bytes": 0}


def get_project(project_id: str) -> Dict:
    for p in _load_registry():
        if p["id"] == project_id:
            return p
    raise KeyError(f"project {project_id} not found")


def delete_project(project_id: str) -> None:
    registry = _load_registry()
    new_registry = [p for p in registry if p["id"] != project_id]
    if len(new_registry) == len(registry):
        raise KeyError(f"project {project_id} not found")
    _save_registry(new_registry)
    project_dir = PROJECTS_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)


# ---------------------------------------------------------------------------
# Per-project paths
# ---------------------------------------------------------------------------

def _project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def _working_dir(project_id: str) -> Path:
    return _project_dir(project_id) / "working"


def _versions_dir(project_id: str) -> Path:
    return _project_dir(project_id) / "versions"


def _manifest_path(project_id: str) -> Path:
    return _project_dir(project_id) / "manifest.json"


def _chunk_store_dir(project_id: str) -> Path:
    return _project_dir(project_id) / "chunk_store"


def _dedup_manifest_path(project_id: str) -> Path:
    return _project_dir(project_id) / "dedup_manifest.json"


def _chunk_path(project_id: str, chunk_hash: str) -> Path:
    # Two-char prefix sharding avoids one giant flat directory -- the same
    # trick Git itself uses for loose objects (.git/objects/xx/rest...).
    return _chunk_store_dir(project_id) / chunk_hash[:2] / chunk_hash


def _assert_project_exists(project_id: str) -> None:
    if not any(p["id"] == project_id for p in _load_registry()):
        raise KeyError(f"project {project_id} not found")


def _ensure_dirs(project_id: str) -> None:
    _working_dir(project_id).mkdir(parents=True, exist_ok=True)
    _versions_dir(project_id).mkdir(parents=True, exist_ok=True)


def _ensure_repo(project_id: str) -> Repo:
    _ensure_dirs(project_id)
    working = _working_dir(project_id)
    if not (working / ".git").exists():
        repo = Repo.init(working)
        repo.index.commit("Initialize repository", author=GIT_AUTHOR, committer=GIT_AUTHOR)
    else:
        repo = Repo(working)
    return repo


def _load_manifest(project_id: str) -> List[Dict]:
    path = _manifest_path(project_id)
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_manifest(project_id: str, manifest: List[Dict]) -> None:
    with open(_manifest_path(project_id), "w") as f:
        json.dump(manifest, f, indent=2)


def _load_dedup_manifest(project_id: str) -> List[Dict]:
    path = _dedup_manifest_path(project_id)
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_dedup_manifest(project_id: str, manifest: List[Dict]) -> None:
    with open(_dedup_manifest_path(project_id), "w") as f:
        json.dump(manifest, f, indent=2)


def _write_chunk_if_new(project_id: str, chunk_bytes: bytes) -> tuple[str, int]:
    """
    Store `chunk_bytes` under its content hash if not already present.
    Returns (hash_hex, bytes_actually_written) -- bytes_actually_written
    is 0 when the chunk already existed, which is exactly the dedup savings.
    """
    chunk_hash = hashlib.sha256(chunk_bytes).hexdigest()
    path = _chunk_path(project_id, chunk_hash)
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
# Versioning operations (all scoped to one project)
# ---------------------------------------------------------------------------

def save_version(project_id: str, uploaded_files: Dict[str, bytes], message: str) -> Dict:
    _assert_project_exists(project_id)
    _ensure_dirs(project_id)
    repo = _ensure_repo(project_id)
    working = _working_dir(project_id)
    versions_dir = _versions_dir(project_id)

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

    manifest = _load_manifest(project_id)
    version_id = len(manifest) + 1

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
    _save_manifest(project_id, manifest)

    # --- O3: content-addressed, deduplicated storage (the CP2 contribution) ---
    # Runs on the SAME uploaded files, sharing this version's id/commit/message,
    # so the two systems land on the same x-axis for direct comparison.
    dedup_files = {}
    new_bytes_written = 0
    for rel_path, content in uploaded_files.items():
        chunk_hashes = []
        for chunk in chunk_content(content):
            chunk_hash, written = _write_chunk_if_new(project_id, chunk)
            chunk_hashes.append(chunk_hash)
            new_bytes_written += written
        dedup_files[rel_path] = {"chunk_hashes": chunk_hashes, "size_bytes": len(content)}

    dedup_manifest = _load_dedup_manifest(project_id)
    # Real disk usage of the chunk store, not an incremental estimate --
    # this is the actual number a KPI-1 comparison has to be honest about.
    cumulative_dedup_bytes = _dir_size_bytes(_chunk_store_dir(project_id))

    dedup_entry = {
        "id": version_id,
        "message": commit_message,
        "commit_hash": commit_hash,
        "created_at": entry["created_at"],
        "file_count": file_count,
        "total_logical_bytes": total_size,       # what it WOULD cost, uncompressed
        "new_bytes_written": new_bytes_written,    # what THIS version actually cost
        "cumulative_dedup_bytes": cumulative_dedup_bytes,
        "files": dedup_files,
    }
    dedup_manifest.append(dedup_entry)
    _save_dedup_manifest(project_id, dedup_manifest)

    return entry


def list_versions(project_id: str) -> List[Dict]:
    _assert_project_exists(project_id)
    return _load_manifest(project_id)


def get_version(project_id: str, version_id: int) -> Dict:
    for entry in _load_manifest(project_id):
        if entry["id"] == version_id:
            return entry
    raise KeyError(f"version {version_id} not found in project {project_id}")


def get_version_files(project_id: str, version_id: int) -> List[Dict]:
    snapshot_dir = _versions_dir(project_id) / f"v{version_id}"
    if not snapshot_dir.exists():
        raise KeyError(f"version {version_id} not found in project {project_id}")
    return _list_files(snapshot_dir)


def get_version_dir(project_id: str, version_id: int) -> Path:
    snapshot_dir = _versions_dir(project_id) / f"v{version_id}"
    if not snapshot_dir.exists():
        raise KeyError(f"version {version_id} not found in project {project_id}")
    return snapshot_dir


def storage_growth(project_id: str) -> List[Dict]:
    _assert_project_exists(project_id)
    return [
        {"version": e["id"], "cumulative_naive_bytes": e["cumulative_naive_bytes"]}
        for e in _load_manifest(project_id)
    ]


def dedup_storage_growth(project_id: str) -> List[Dict]:
    _assert_project_exists(project_id)
    return [
        {"version": e["id"], "cumulative_dedup_bytes": e["cumulative_dedup_bytes"]}
        for e in _load_dedup_manifest(project_id)
    ]


def get_dedup_version(project_id: str, version_id: int) -> Dict:
    for entry in _load_dedup_manifest(project_id):
        if entry["id"] == version_id:
            return entry
    raise KeyError(f"dedup version {version_id} not found in project {project_id}")


def reconstruct_version_files(project_id: str, version_id: int) -> Dict[str, bytes]:
    """
    Rebuild every file in a version purely from stored chunks -- this is
    the O4 "efficient retrieval" proof: the dedup store isn't just a size
    trick, it can actually reproduce the exact original bytes on demand.
    """
    entry = get_dedup_version(project_id, version_id)
    result = {}
    for rel_path, file_info in entry["files"].items():
        pieces = []
        for chunk_hash in file_info["chunk_hashes"]:
            path = _chunk_path(project_id, chunk_hash)
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


def diff_versions(project_id: str, from_id: int, to_id: int) -> List[Dict]:
    from_dir = get_version_dir(project_id, from_id)
    to_dir = get_version_dir(project_id, to_id)

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


def git_log(project_id: str) -> List[Dict]:
    _assert_project_exists(project_id)
    repo = _ensure_repo(project_id)
    entries = []
    for commit in repo.iter_commits():
        entries.append({
            "hash": commit.hexsha[:10],
            "message": commit.message.strip(),
            "author": commit.author.name,
            "date": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat(),
        })
    return entries
