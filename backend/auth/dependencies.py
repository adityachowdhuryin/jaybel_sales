"""FastAPI auth dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.firebase_verifier import verify_id_token
from backend.db import postgres as db

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    firebase_uid: str
    email: str | None
    display_name: str | None
    sales_rep_code: str | None


def _auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "").lower() in ("1", "true", "yes")


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if _auth_disabled():
        row = db.get_user(os.getenv("DEFAULT_USER_ID", "00000000-0000-4000-8000-000000000001"))
        return CurrentUser(
            id=row["id"],
            firebase_uid=row.get("firebase_uid") or "local-dev",
            email=row.get("email"),
            display_name=row.get("display_name"),
            sales_rep_code=row.get("sales_rep_code"),
        )

    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(401, "Missing or invalid Authorization header")

    try:
        identity = verify_id_token(creds.credentials)
    except Exception as exc:
        raise HTTPException(401, f"Invalid token: {exc}") from exc

    row = db.get_or_create_user_by_firebase_uid(
        firebase_uid=identity.uid,
        email=identity.email,
        display_name=identity.name,
    )
    return CurrentUser(
        id=row["id"],
        firebase_uid=identity.uid,
        email=row.get("email"),
        display_name=row.get("display_name"),
        sales_rep_code=row.get("sales_rep_code"),
    )
