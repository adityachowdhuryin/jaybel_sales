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

from pipeline.guard_runner import load_guard_cases, run_guard_checks, summarize_guard


def main() -> None:
    p = argparse.ArgumentParser(description="Jaybel QA suite runner")
    p.add_argument("--cases", default="Q061-Q097", help="Q061-Q097 or comma-separated ids")
    p.add_argument(
        "--mode",
        choices=["keyword", "routing", "sql_validate", "guard", "sql_regression"],
        default="keyword",
        help="keyword=CI-safe; routing/sql_validate=Vertex L1/L2; guard=scope gates; sql_regression=offline SQL QA",
    )
    p.add_argument("--source", default=None, help="Filter by source e.g. office_supplies_bi_pdf")
    p.add_argument("--json-out", default=None, help="Write summary JSON to path")
    args = p.parse_args()

    if args.mode == "guard":
        cases = load_guard_cases(case_filter=args.cases, source=args.source)
        results = run_guard_checks(cases)
        summary = summarize_guard(results)
        print(json.dumps(summary, indent=2))
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )
        if summary["guard_match"] < summary["total"]:
            sys.exit(1)
        return

    if args.mode == "sql_regression":
        from pipeline.sql_regression_runner import (
            load_sql_regression_cases,
            run_sql_offline,
            summarize_sql_regression,
        )

        cases = load_sql_regression_cases(case_filter=args.cases, source=args.source)
        results = run_sql_offline(cases)
        summary = summarize_sql_regression(results)
        print(json.dumps(summary, indent=2))
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )
        if summary["validation_passed"] < summary["total"]:
            sys.exit(1)
        return

    from pipeline.qa_runner import (
        load_cases,
        run_routing_keyword_only,
        run_sql_validation,
        summarize,
    )

    cases = load_cases(case_filter=args.cases, source=args.source)
    if args.mode == "keyword":
        results = run_routing_keyword_only(cases)
        summary = summarize(results)
        failed = summary["table_match"] < summary["total"]
    elif args.mode == "routing":
        results = run_sql_validation(cases, generate_sql=False)
        summary = summarize(results)
        failed = summary["table_match"] < summary["total"]
    else:
        results = run_sql_validation(cases, generate_sql=True)
        summary = summarize(results)
        failed = summary["table_match"] < summary["total"]

    print(json.dumps(summary, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
