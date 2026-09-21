"""
CLOUD-119 -- Data Version Control With Storage Efficiency Across Large Artefacts
CP1 prototype backend. Every version endpoint is scoped under a project id,
so multiple independent projects can be tracked side by side without
sharing working trees, Git history, or storage.
"""
import io
import zipfile
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import versioning
from .schemas import (
    ProjectSummary, CreateProjectRequest,
    VersionSummary, VersionDetail, StoragePoint, DedupStoragePoint, DiffResponse, SaveVersionResponse
)

app = FastAPI(
    title="DVC Capstone Prototype API",
    description="CP1 naive versioning baseline for CLOUD-119 -- multi-project",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@app.get("/api/projects", response_model=List[ProjectSummary])
def get_projects():
    return versioning.list_projects()


@app.post("/api/projects", response_model=ProjectSummary)
def post_project(body: CreateProjectRequest):
    try:
        return versioning.create_project(body.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/projects/{project_id}")
def remove_project(project_id: str):
    try:
        versioning.delete_project(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Versions (all scoped under /api/projects/{project_id}/...)
# ---------------------------------------------------------------------------

@app.post("/api/projects/{project_id}/versions", response_model=SaveVersionResponse)
async def create_version(
    project_id: str,
    message: str = Form(...),
    files: List[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    uploaded = {}
    for f in files:
        content = await f.read()
        rel_path = f.filename.replace("\\", "/")
        uploaded[rel_path] = content

    try:
        entry = versioning.save_version(project_id, uploaded, message)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"version": entry}


@app.get("/api/projects/{project_id}/versions", response_model=List[VersionSummary])
def get_versions(project_id: str):
    try:
        return versioning.list_versions(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/versions/{version_id}", response_model=VersionDetail)
def get_version_detail(project_id: str, version_id: int):
    try:
        entry = versioning.get_version(project_id, version_id)
        files = versioning.get_version_files(project_id, version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found")
    return {**entry, "files": files}


@app.get("/api/projects/{project_id}/versions/{version_id}/download")
def download_version(project_id: str, version_id: int):
    try:
        snapshot_dir = versioning.get_version_dir(project_id, version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in snapshot_dir.rglob("*"):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(snapshot_dir).as_posix())
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{project_id}-version-{version_id}.zip"'},
    )


@app.get("/api/projects/{project_id}/stats/storage-growth", response_model=List[StoragePoint])
def storage_growth(project_id: str):
    try:
        return versioning.storage_growth(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/stats/dedup-growth", response_model=List[DedupStoragePoint])
def dedup_growth(project_id: str):
    try:
        return versioning.dedup_storage_growth(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/versions/{version_id}/download-dedup")
def download_version_from_dedup(project_id: str, version_id: int):
    """
    Same output as /download, but reconstructed purely from the
    content-addressed chunk store -- proves retrieval actually works,
    not just that the size numbers look good.
    """
    try:
        files = versioning.reconstruct_version_files(project_id, version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, content in files.items():
            zf.writestr(rel_path, content)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{project_id}-v{version_id}-dedup.zip"'},
    )


@app.get("/api/projects/{project_id}/diff", response_model=DiffResponse)
def diff(project_id: str, from_version: int, to_version: int):
    try:
        files = versioning.diff_versions(project_id, from_version, to_version)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project or version not found")
    return {"from_version": from_version, "to_version": to_version, "files": files}


@app.get("/api/projects/{project_id}/git-log")
def get_git_log(project_id: str):
    try:
        return versioning.git_log(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
