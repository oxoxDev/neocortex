#!/usr/bin/env bash
# Run the Publish Python SDK workflow locally with act (https://github.com/nektos/act).
# Requires: act installed, and .github/scripts/secrets.json with PYPI_API_TOKEN.
#
# Usage:
#   ./act-publish-python-sdk.sh    # simulate push to main (triggers publish)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SECRETS_FILE="$SCRIPT_DIR/secrets.json"
WORKFLOW=".github/workflows/publish-python-sdk.yml"

if [[ ! -f "$SECRETS_FILE" ]]; then
  echo "Missing $SECRETS_FILE (see secrets.json.example or add PYPI_API_TOKEN)." >&2
  exit 1
fi

cd "$REPO_ROOT"

act push \
  -W "$WORKFLOW" \
  --secret-file "$SECRETS_FILE" \
  -e "$SCRIPT_DIR/push-event.json"
