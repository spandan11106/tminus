#!/usr/bin/env bash
# Shared settings for tminus shell scripts. Rename the plugin by editing PLUGIN_NAME here
# and in .claude-plugin/plugin.json, then grep for the old name.
PLUGIN_NAME="tminus"
TMINUS_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMINUS_ROOT="$(dirname "$TMINUS_SCRIPTS")"
TMINUS_VENV="${TMINUS_VENV:-$HOME/.cache/$PLUGIN_NAME/venv}"
tminus_python() {
  if [ -x "$TMINUS_VENV/bin/python" ]; then echo "$TMINUS_VENV/bin/python"
  elif command -v python3 >/dev/null 2>&1; then command -v python3
  else echo "python3"; fi
}
