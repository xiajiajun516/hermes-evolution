#!/usr/bin/env bash
# ==============================================================================
# Hermes Evolution Log — One-click Update Script
# ==============================================================================
# Usage:
#   ./update.sh               # Run standard incremental update
#   ./update.sh --baseline    # Initialize baseline snapshot (no diff output)
#   ./update.sh --full-rebuild # Perform full rebuild (compress records older than 3 months)
#   ./update.sh --project foo # Specify project name explicitly
# ==============================================================================

set -e

# Resolve repository root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧬 Hermes Evolution Log — Updating Dashboard..."

# Detect valid Python executable
PYTHON_CMD=""
for cmd in "python" "py -3" "python3"; do
  if $cmd -c "import sys" &>/dev/null; then
    PYTHON_CMD="$cmd"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  echo "❌ Error: Python 3 executable not found!" >&2
  exit 1
fi

# Execute generator script with CLI arguments passed through
$PYTHON_CMD generate.py "$@"

echo ""
echo "✅ Update complete! Dashboard updated at: output/index.html"
