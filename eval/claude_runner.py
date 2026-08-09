import json
import subprocess
from typing import Optional


class ClaudeRunError(Exception):
    pass


def run_claude(
    prompt: str,
    cwd: str,
    session_id: Optional[str] = None,
    mcp_config_path: Optional[str] = None,
    json_schema: Optional[str] = None,
    timeout: int = 180,
) -> dict:
    """
    Runs `claude -p` headlessly in `cwd` and returns the parsed JSON result
    dict (fields include `session_id`, `result`, `total_cost_usd`, ...).
    stdout/stderr are captured separately -- a hook's stderr output racing
    with the JSON stdout stream corrupted parsing in early testing.
    """
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ]
    if session_id:
        cmd += ["--session-id", session_id]
    if mcp_config_path:
        cmd += ["--strict-mcp-config", "--mcp-config", mcp_config_path]
    if json_schema:
        cmd += ["--json-schema", json_schema]

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise ClaudeRunError(f"claude -p exited {result.returncode}: {result.stderr[:1000]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ClaudeRunError(f"Failed to parse claude -p JSON output: {e}\nstdout[:1000]={result.stdout[:1000]}")
