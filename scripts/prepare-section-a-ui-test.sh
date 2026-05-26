#!/usr/bin/env bash
# Legacy alias — use scripts/prepare-ui-test.sh
exec "$(cd "$(dirname "$0")/.." && pwd)/scripts/prepare-ui-test.sh" "$@"
