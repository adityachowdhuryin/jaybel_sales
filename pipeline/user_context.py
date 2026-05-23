"""Optional caller context (from local Postgres user / Phase C API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
                " When the user says 'my' / 'mine' / 'my sales' / 'my GP', filter to this "
                "rep via dim_sales_rep (sales_rep_code or rep_key) joined to the fact table. "
                "For closed-won / closed deals / payout: sum line_sales_ex_gst or line_gp_dollar "
                "on fact_sales_report for this rep in the requested month or fiscal quarter."
            )
        return f"\nAuthenticated user context: {', '.join(parts)}.{rep_note}\n"
