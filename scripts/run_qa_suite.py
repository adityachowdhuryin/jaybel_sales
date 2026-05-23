#!/usr/bin/env python3
"""Run QA evaluation cases (routing keyword-only or full L1 via Vertex)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.qa_runner import load_cases, run_routing_keyword_only, run_sql_validation, summarize


def main() -> None:
    p = argparse.ArgumentParser(description="Jaybel QA suite runner")
    p.add_argument("--cases", default="Q061-Q097", help="Q061-Q097 or comma-separated ids")
    p.add_argument(
        "--mode",
        choices=["keyword", "routing", "sql_validate"],
        default="keyword",
        help="keyword=CI-safe; routing/sql_validate=Vertex L1/L2",
    )
    p.add_argument("--source", default=None, help="Filter by source e.g. office_supplies_bi_pdf")
    p.add_argument("--json-out", default=None, help="Write summary JSON to path")
    args = p.parse_args()

    cases = load_cases(case_filter=args.cases, source=args.source)
    if args.mode == "keyword":
        results = run_routing_keyword_only(cases)
    elif args.mode == "routing":
        results = run_sql_validation(cases, generate_sql=False)
    else:
        results = run_sql_validation(cases, generate_sql=True)

    summary = summarize(results)
    print(json.dumps(summary, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if summary["table_match"] < summary["total"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
