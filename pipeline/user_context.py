"""Optional caller context (from local Postgres user / Phase C API)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pipeline.query_understanding_config import rep_patterns

# "my commission" / "my payout" stay rep-scoped; other "my" → company ("our").
_REP_SCOPED_MY_RE = re.compile(
    r"\bmy\s+(?:commission|payout)\b",
    re.I,
)
_MY_WORD_RE = re.compile(r"\bmy\b", re.I)
_MINE_WORD_RE = re.compile(r"\bmine\b", re.I)


@dataclass
class UserContext:
    user_id: str | None = None
    sales_rep_code: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> UserContext:
        if not data:
            return cls()
        return cls(
            user_id=data.get("user_id") or None,
            sales_rep_code=data.get("sales_rep_code") or None,
        )

    def prompt_block(self) -> str:
        parts: list[str] = []
        if self.user_id:
            parts.append(f"user_id={self.user_id}")
        if self.sales_rep_code:
            parts.append(f"sales_rep_code={self.sales_rep_code}")
        if not parts:
            return ""
        rep_note = ""
        if self.sales_rep_code:
            rep_note = (
                " Treat 'my' / 'our' / company-wide questions as all-rep totals (no rep filter). "
                "Filter to this rep only when the user asks about their commission, payout, "
                "closed-won deals, or uses first-person 'I' for personal sales (see rep patterns). "
                "Join via dim_sales_rep (sales_rep_code or rep_key)."
            )
        return f"\nAuthenticated user context: {', '.join(parts)}.{rep_note}\n"


def is_rep_scoped_my_phrase(question: str) -> bool:
    return bool(_REP_SCOPED_MY_RE.search(question))


def normalize_company_possessive(question: str) -> str:
    """Map general 'my' / 'mine' to 'our' (company-wide). Keeps my commission/payout unchanged."""
    if not question or not (_MY_WORD_RE.search(question) or _MINE_WORD_RE.search(question)):
        return question

    protected: list[str] = []

    def _shield(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return f"__REP_SCOPE_{len(protected) - 1}__"

    shielded = _REP_SCOPED_MY_RE.sub(_shield, question)
    shielded = _MY_WORD_RE.sub("our", shielded)
    shielded = _MINE_WORD_RE.sub("ours", shielded)
    for i, phrase in enumerate(protected):
        shielded = shielded.replace(f"__REP_SCOPE_{i}__", phrase)
    return shielded


def requires_rep_scope(question: str) -> bool:
    q = question.lower()
    if is_rep_scoped_my_phrase(question):
        return True
    for pattern in rep_patterns():
        if pattern.lower() in q:
            return True
    return False


def rep_gate_message() -> str:
    return (
        "This question needs your **sales rep code** for commission, payout, or "
        "personal closed-deal totals. Set it in the sidebar under Settings, then ask again."
    )
