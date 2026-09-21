## Data Version Control With Storage Efficiency Across Large Artefacts

A working full-stack system with **two storage engines running side by
side** on the same uploaded files, so their storage cost can be compared
directly — which is the whole point of the capstone:

- **O2 naive baseline** — a full copy of every file, every version. Real
  Git commits, deliberately inefficient, this is the reference everything
  else is measured against.
- **O3 content-addressed store** — files are split into content-defined
  chunks (a rolling-hash chunker, `backend/app/chunking.py`), each chunk
  is hashed (SHA-256) and stored once; unchanged chunks across versions
  are never written again. Storage grows with **distinct content**, not
  with version count.

Multiple independent **projects** are supported — each with its own
working tree, Git history, naive snapshots, and chunk store, fully
isolated from every other project.

---

## Architecture

```
React frontend (Vite)  <--HTTP/JSON-->  FastAPI backend
                                              │
                     data/projects/<project_id>/
                                              │
                     ├── working/            <- real Git repo
                     ├── versions/v1, v2...   <- O2: full-copy snapshots
                     ├── manifest.json        <- O2 metadata
                     ├── chunk_store/xx/...   <- O3: content-addressed chunks
                     └── dedup_manifest.json  <- O3 metadata (file -> chunk hashes)
```

Every "Save version" does, in one action:
1. Writes uploaded files into `working/` and makes a real `git commit`.
2. **O2:** copies the entire working tree into `versions/vN/` (naive, full-copy).
3. **O3:** splits each file into content-defined chunks, writes only
   chunks not already in `chunk_store/`, and records each file's ordered
   chunk-hash list in `dedup_manifest.json`.

Both engines share the same version id, commit hash, and timestamp, so
their storage numbers land on the same x-axis for direct comparison —
that's what the Overview page's chart shows.

---

## The chunking algorithm (`backend/app/chunking.py`)

A simplified Gear-hash content-defined chunker: chunk boundaries are
found by content (a rolling hash), not fixed byte offsets. This matters —
insert one byte at the start of a file and a fixed-size chunker's *every*
subsequent block shifts and re-hashes as "new," destroying all dedup
benefit. Content-defined chunking resyncs within roughly one average
chunk size after an edit, so only the chunks actually touched by a change
are re-stored.

Known limitation, documented honestly: on highly repetitive input (the
same block copy-pasted many times back to back) the simplified rolling
hash can fall into a periodic cycle and miss boundaries, degrading to the
hard `MAX_CHUNK_SIZE` cutoff. This doesn't show up on realistic code —
verified against a real 11KB source file with a one-line edit, which
produced 30% savings with 22 of 36 chunks reused. A production system
would use FastCDC's normalized chunking (two masks) to close this gap;
noted here as a deliberate, documented scope decision for CP1/CP2 rather
than an oversight.

---

## Running it locally

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

OR TRY THIS

uvicorn app.main:app --reload --reload-dir app --port 8000
```

Backend runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`, talking to the backend via
`VITE_API_BASE` in `frontend/.env` (defaults to `http://localhost:8000`).

---

## What to demo

1. **Create a project**, then save a version with a few real source files
   (a few KB each — the dedup effect is subtle on tiny toy files, same as
   real systems).
2. **Save a second version** with a small, realistic edit to one file.
   Watch the Overview chart: the naive (red) line jumps by the full file
   size; the dedup (teal) line only grows by the size of the chunks that
   actually changed.
3. **Stats bar** shows the running "storage saved %" — this is your
   KPI-1 number, computed live, not hardcoded.
4. **Version history → diff** still works exactly as before (untouched
   by this change) — file-level added/modified/unchanged status.
5. **Git log** — still real commits; the O3 engine didn't touch Git at all.
6. Optionally hit `GET /api/projects/{id}/versions/{id}/download-dedup`
   in the API docs — this reconstructs the version purely from stored
   chunks, proving the dedup store isn't just a size trick, it actually
   round-trips to the exact original bytes (verified byte-for-byte in
   testing across multiple versions).

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/projects` | List / create projects |
| DELETE | `/api/projects/{id}` | Delete a project and all its data |
| POST | `/api/projects/{id}/versions` | Save a new version (both engines) |
| GET | `/api/projects/{id}/versions` | List versions |
| GET | `/api/projects/{id}/versions/{vid}` | Version detail + file list |
| GET | `/api/projects/{id}/versions/{vid}/download` | Download from **naive** snapshot |
| GET | `/api/projects/{id}/versions/{vid}/download-dedup` | Download reconstructed from **chunks** |
| GET | `/api/projects/{id}/stats/storage-growth` | O2 cumulative storage per version |
| GET | `/api/projects/{id}/stats/dedup-growth` | O3 cumulative storage per version |
| GET | `/api/projects/{id}/diff` | File-level diff between two versions |
| GET | `/api/projects/{id}/git-log` | Real git commit history |

## What's next (further CP2 work)

- Fault-injection tests (NT1–NT5 from the spec): corrupt/delete a chunk,
  simulate a crash mid-write, prove safe degraded behavior and recovery.
- p50/p95/p99 retrieval latency measurement over repeated trials (KPI-2).
- Optional: swap `chunk_store/` for an S3/MinIO backend behind the same
  `_write_chunk_if_new` / chunk-read interface — the rest of the system
  wouldn't need to change.
