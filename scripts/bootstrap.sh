#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCAN_AI_RADAR_VENV:-/tmp/scan-ai-radar-venv}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found in PATH" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

cat <<EOF
scan-ai-radar bootstrap complete.

Venv: $VENV_DIR
Python: $VENV_DIR/bin/python

Example:
  export no_proxy='*' NO_PROXY='*'
  cd "$SCRIPT_DIR"
  "$VENV_DIR/bin/python" cdp.py "https://x.com/OpenAI" --port 9223 --scrolls 2 --json
EOF
