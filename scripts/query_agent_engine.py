#!/usr/bin/env python3
"""Smoke-test a deployed Agent Engine with one question."""

from __future__ import annotations

import argparse
import os
import sys

import vertexai
from vertexai import agent_engines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", default=os.environ.get("AGENT_ENGINE_RESOURCE", ""))
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", "jaybel-dev"))
    parser.add_argument("--region", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    parser.add_argument("--question", default="How many departments are in Jaybel?")
    args = parser.parse_args()

    if not args.resource:
        print("Set --resource or AGENT_ENGINE_RESOURCE", file=sys.stderr)
        sys.exit(1)

    vertexai.init(project=args.project, location=args.region)
    engine = agent_engines.get(args.resource)
    session = engine.create_session(user_id="smoke-test")
    for event in engine.stream_query(
        user_id="smoke-test",
        session_id=session["id"],
        message=args.question,
    ):
        print(event)


if __name__ == "__main__":
    main()
