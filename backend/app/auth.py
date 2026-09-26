"""
Verifies the Supabase Auth access token sent by the frontend and extracts
the user's id -- every API route depends on this, so an unauthenticated
or forged request never reaches versioning.py.

Handles BOTH Supabase signing modes, since which one your project uses
depends on when it was created and isn't something the backend should
have to be told:
  - ES256 (current default): verified with the project's public key,
    fetched once from the JWKS endpoint and cached -- no secret needed.
  - HS256 (legacy): verified with the shared secret from
    SUPABASE_JWT_SECRET, if one was provided.

The token's header names which algorithm it was signed with, so we read
that first (without trusting it for verification itself) and route to
the matching check.
"""
import jwt
from fastapi import Header, HTTPException
from .config import SUPABASE_JWT_SECRET, SUPABASE_JWKS_URL

# Built once at import time so the JWKS response is cached across
# requests (PyJWKClient caches internally) instead of re-fetched every
# single call.
_jwks_client = jwt.PyJWKClient(SUPABASE_JWKS_URL, cache_keys=True)


def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Malformed token: {e}")

    alg = header.get("alg")

    try:
        if alg == "HS256":
            if not SUPABASE_JWT_SECRET:
                raise HTTPException(
                    status_code=401,
                    detail="Token is HS256 but SUPABASE_JWT_SECRET is not configured on the backend",
                )
            payload = jwt.decode(
                token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated"
            )
        else:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=["ES256", "RS256"], audience="authenticated"
            )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    return payload["sub"]  # Supabase Auth's user id (uuid)