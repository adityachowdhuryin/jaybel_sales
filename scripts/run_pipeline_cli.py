#!/usr/bin/env python3
"""CLI to run one question through the pipeline (Phase A smoke test)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.pipeline import Pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="How many rows in dim_department?")
    parser.add_argument("--skip-execute", action="store_true")
    args = parser.parse_args()

    p = Pipeline()
    result = p.run(args.question, skip_execute=args.skip_execute)
    for ev in result.events:
        print(json.dumps(ev.to_dict(), default=str))
    if result.sql:
        print("\n--- SQL ---\n", result.sql, file=sys.stderr)


if __name__ == "__main__":
    main()
