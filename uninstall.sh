#!/usr/bin/env bash
# Removes everything setup.sh installed: the global Claude Code/agy
# integration (slash commands/skills, hooks, MCP registration), the
# dedicated venv, and the ~/.local/bin/session-memory symlink.
#
# By default, every registered workspace's own .conversation-memory/ data
# and the global registry are LEFT IN PLACE. Pass --purge-data to also
# delete those (you'll be prompted per-workspace before anything is
# deleted).
#
# Usage:
#   ./uninstall.sh                # remove the framework, keep conversation data
#   ./uninstall.sh --purge-data   # remove the framework AND all conversation data
set -euo pipefail

INSTALL_ROOT="$HOME/.local/share/session-memory"
VENV_DIR="$INSTALL_ROOT/venv"
BIN_LINK="$HOME/.local/bin/session-memory"

PURGE_DATA=""
for arg in "$@"; do
  case "$arg" in
    --purge-data) PURGE_DATA="--purge-data" ;;
    *) echo "Unknown argument: $arg (only --purge-data is supported)" >&2; exit 1 ;;
  esac
done

echo "== session-memory uninstall =="

if [ -x "$VENV_DIR/bin/session-memory" ]; then
  echo "-- Unwiring global integration (Claude Code + agy) --"
  # Runs while the venv still exists, since this is what does the actual
  # Claude Code / agy config unwiring in Python.
  "$VENV_DIR/bin/session-memory" setup uninstall $PURGE_DATA
else
  echo "No venv found at $VENV_DIR -- skipping config unwiring (nothing installed, or already removed)."
fi

echo
echo "-- Removing install footprint --"
if [ -L "$BIN_LINK" ] || [ -e "$BIN_LINK" ]; then
  rm -f "$BIN_LINK"
  echo "  removed $BIN_LINK"
fi
if [ -d "$INSTALL_ROOT" ]; then
  rm -rf "$INSTALL_ROOT"
  echo "  removed $INSTALL_ROOT"
fi

echo
echo "== Done =="
if [ -z "$PURGE_DATA" ]; then
  echo "Conversation memory data in each project's own .conversation-memory/ was left in place."
  echo "Re-run with --purge-data to also delete it (and the global registry)."
fi
