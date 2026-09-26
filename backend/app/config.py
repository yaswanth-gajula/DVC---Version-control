"""
Loads what the backend needs to verify Supabase Auth tokens locally.

Supabase projects sign tokens one of two ways depending on when the
project was created / whether "JWT Signing Keys" has been migrated:
  - Legacy: HS256, verified with a shared secret (SUPABASE_JWT_SECRET)
  - Current default: ES256, verified with a public key fetched from the
    project's JWKS endpoint (needs only SUPABASE_URL, no secret at all)

We support both so this works regardless of which mode your project is
in -- see auth.py. SUPABASE_URL is required; SUPABASE_JWT_SECRET is
optional and only used as a fallback for legacy HS256 tokens.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy backend/.env.example to backend/.env and fill it in."
        )
    return value


SUPABASE_URL = _require("SUPABASE_URL").rstrip("/")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")  # optional, legacy fallback
SUPABASE_JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"