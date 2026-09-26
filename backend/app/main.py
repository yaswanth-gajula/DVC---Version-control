"""
CLOUD-119 -- Data Version Control With Storage Efficiency Across Large Artefacts

Every route below (except /api/health) depends on get_current_user_id,
which verifies the Supabase Auth access token the frontend sends in the
Authorization header. Supabase is used ONLY for authentication -- the
extracted user id is used purely to partition LOCAL DISK storage (see
versioning.py), so a user can only ever see or touch their own projects.
No project, version, or chunk data is ever sent to Supabase.
"""
import io
import zipfile
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import versioning
from .auth import get_current_user_id
from .schemas import (
    ProjectSummary, CreateProjectRequest,
    VersionSummary, VersionDetail, StoragePoint, DedupStoragePoint, DiffResponse, SaveVersionResponse
)

app = FastAPI(
    title="DVC Capstone Prototype API",
    description="CLOUD-119 -- multi-project, multi-user (Supabase Auth only; all data local)",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prototype only -- tighten to your frontend's origin before any real deployment
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
def get_projects(user_id: str = Depends(get_current_user_id)):
    return versioning.list_projects(user_id)


@app.post("/api/projects", response_model=ProjectSummary)
def post_project(body: CreateProjectRequest, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.create_project(user_id, body.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/projects/{project_id}")
def remove_project(project_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        versioning.delete_project(user_id, project_id)
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
    user_id: str = Depends(get_current_user_id),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    uploaded = {}
    for f in files:
        content = await f.read()
        rel_path = f.filename.replace("\\", "/")
        uploaded[rel_path] = content

    try:
        entry = versioning.save_version(user_id, project_id, uploaded, message)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"version": entry}


@app.get("/api/projects/{project_id}/versions", response_model=List[VersionSummary])
def get_versions(project_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.list_versions(user_id, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/versions/{version_id}", response_model=VersionDetail)
def get_version_detail(project_id: str, version_id: int, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.get_version(user_id, project_id, version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found")


@app.get("/api/projects/{project_id}/versions/{version_id}/download")
def download_version(project_id: str, version_id: int, user_id: str = Depends(get_current_user_id)):
    try:
        snapshot_dir = versioning.download_naive_zip(user_id, project_id, version_id)
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


@app.get("/api/projects/{project_id}/versions/{version_id}/download-dedup")
def download_version_from_dedup(project_id: str, version_id: int, user_id: str = Depends(get_current_user_id)):
    """
    Same output as /download, but reconstructed purely from the
    content-addressed chunk store -- proves retrieval actually works,
    not just that the size numbers look good.
    """
    try:
        files = versioning.reconstruct_version_files(user_id, project_id, version_id)
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


@app.get("/api/projects/{project_id}/stats/storage-growth", response_model=List[StoragePoint])
def storage_growth(project_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.storage_growth(user_id, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/stats/dedup-growth", response_model=List[DedupStoragePoint])
def dedup_growth(project_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.dedup_storage_growth(user_id, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@app.get("/api/projects/{project_id}/diff", response_model=DiffResponse)
def diff(project_id: str, from_version: int, to_version: int, user_id: str = Depends(get_current_user_id)):
    try:
        files = versioning.diff_versions(user_id, project_id, from_version, to_version)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project or version not found")
    return {"from_version": from_version, "to_version": to_version, "files": files}


@app.get("/api/projects/{project_id}/git-log")
def get_git_log(project_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        return versioning.git_log(user_id, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")