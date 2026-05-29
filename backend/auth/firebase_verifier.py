"""Verify Firebase ID tokens."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from backend.config import settings


@dataclass(frozen=True)
class FirebaseIdentity:
    uid: str
    email: str | None
    name: str | None


@lru_cache(maxsize=1)
def _ensure_firebase_app() -> None:
    if firebase_admin._apps:
        return
    project = settings()["firebase_project_id"]
    try:
        firebase_admin.initialize_app(
            credentials.ApplicationDefault(),
            options={"projectId": project},
        )
    except Exception:
        firebase_admin.initialize_app(options={"projectId": project})


def verify_id_token(token: str) -> FirebaseIdentity:
    _ensure_firebase_app()
    decoded = firebase_auth.verify_id_token(token, check_revoked=True)
    return FirebaseIdentity(
        uid=decoded["uid"],
        email=decoded.get("email"),
        name=decoded.get("name"),
    )
