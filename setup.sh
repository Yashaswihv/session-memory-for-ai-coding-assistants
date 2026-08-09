#!/usr/bin/env bash
# Installs session-memory globally: a dedicated venv (independent of this
# repo checkout's location), a `session-memory` binary on your PATH, and
# global integration into both Claude Code and agy (slash commands/skills,
# lifecycle hooks, MCP registration). Safe to re-run -- every step is
# idempotent.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$HOME/.local/share/session-memory"
VENV_DIR="$INSTALL_ROOT/venv"
BIN_LINK="$HOME/.local/bin/session-memory"

echo "== session-memory setup =="
echo "Repo: $REPO_DIR"
echo "Venv: $VENV_DIR"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required and wasn't found on PATH." >&2
  exit 1
fi

echo "-- Creating dedicated venv --"
python3 -m venv "$VENV_DIR"

echo "-- Installing session-memory into it (this can take a minute -- pulls in faiss/sentence-transformers) --"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install "$REPO_DIR" -q

echo
echo "-- Wiring global integration --"
"$VENV_DIR/bin/session-memory" setup install --bin-path "$VENV_DIR/bin/session-memory"

echo
echo "== Done =="
echo "session-memory installed at: $BIN_LINK"
case ":$PATH:" in
  *":$HOME/.local/bin:"*)
    echo "Verify with: session-memory --version"
    ;;
  *)
    echo "NOTE: $HOME/.local/bin is not currently on your PATH."
    echo '  Add this to your shell profile: export PATH="$HOME/.local/bin:$PATH"'
    echo "  Until then, use the full path: $BIN_LINK --version"
    ;;
esac
echo
echo "Next: open any project in Claude Code or agy and run /initialize-conversation-memory"
echo "(or the equivalent agy skill) to opt that directory in."
