"""Chat retry / turn deletion tests."""

from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Set DATABASE_URL to run DB tests",
)


@pytest.fixture
def db_user_session():
    from tests.conftest_backend import apply_backend_test_env

    apply_backend_test_env()
    from backend.db import postgres as db

    uid = str(uuid.uuid4())
    user = db.ensure_user(uid, email="retry-test@example.com", display_name="Retry Test")
    session = db.create_session(user["id"], title="Retry test")
    turn = db.insert_turn(
        str(session["id"]),
        {
            "query_id": str(uuid.uuid4()),
            "question": "What is sales?",
            "answer": "old answer",
            "row_count": 0,
        },
    )
    yield user, session, turn
    try:
        db.delete_session(str(session["id"]), user["id"])
    except LookupError:
        pass


def test_delete_turn(db_user_session):
    from backend.db import postgres as db

    user, session, turn = db_user_session
    session_id = str(session["id"])
    turn_id = str(turn["id"])

    db.delete_turn(session_id, turn_id, user["id"])
    turns = db.list_turns(session_id)
    assert all(str(t["id"]) != turn_id for t in turns)


def test_delete_turn_wrong_user_raises(db_user_session):
    from backend.db import postgres as db

    _user, session, turn = db_user_session
    other = str(uuid.uuid4())
    db.ensure_user(other, email="other@example.com", display_name="Other")

    with pytest.raises(LookupError):
        db.delete_turn(str(session["id"]), str(turn["id"]), other)
