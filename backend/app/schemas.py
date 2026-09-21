"""
Pydantic models describing every shape of data that crosses the API boundary.
"""
from typing import List, Optional
from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: str                 # URL-safe slug, e.g. "billing-service"
    name: str                # display name, e.g. "Billing Service"
    created_at: str
    version_count: int
    total_bytes: int


class CreateProjectRequest(BaseModel):
    name: str


class FileEntry(BaseModel):
    path: str
    size_bytes: int


class VersionSummary(BaseModel):
    id: int
    message: str
    commit_hash: str
    created_at: str
    file_count: int
    total_size_bytes: int
    cumulative_naive_bytes: int


class VersionDetail(VersionSummary):
    files: List[FileEntry]


class StoragePoint(BaseModel):
    version: int
    cumulative_naive_bytes: int


class DedupStoragePoint(BaseModel):
    version: int
    cumulative_dedup_bytes: int


class FileDiffEntry(BaseModel):
    path: str
    status: str
    diff: Optional[str] = None


class DiffResponse(BaseModel):
    from_version: int
    to_version: int
    files: List[FileDiffEntry]


class SaveVersionResponse(BaseModel):
    version: VersionSummary
