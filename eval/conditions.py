import json
import os
import subprocess

from eval.claude_runner import run_claude
from eval.scenarios import Scenario

SM_BIN = os.environ.get(
    "SESSION_MEMORY_BIN",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "bin", "session-memory"),
)


def _find_transcript_path(session_id: str) -> str:
    matches = subprocess.run(
        ["find", os.path.expanduser("~/.claude/projects"), "-name", f"{session_id}.jsonl"],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    if not matches:
        raise RuntimeError(f"No transcript found for session {session_id}")
    return matches[0]


def run_condition_c0(scenario: Scenario, workdir: str) -> dict:
    """No memory at all: fresh empty directory, no AGENTS.md, no MCP, no hooks."""
    os.makedirs(workdir, exist_ok=True)
    dev2_result = run_claude(scenario.dev2_task, cwd=workdir)
    return {"condition": "C0", "dev2_result": dev2_result, "workdir": workdir}


def run_condition_c1(scenario: Scenario, workdir: str) -> dict:
    """Static AGENTS.md only, written once, never dynamically updated --
    the paper's 'existing mitigation' baseline."""
    os.makedirs(workdir, exist_ok=True)
    with open(os.path.join(workdir, "AGENTS.md"), "w", encoding="utf-8") as f:
        f.write(scenario.static_doc_text)
    dev2_result = run_claude(scenario.dev2_task, cwd=workdir)
    return {"condition": "C1", "dev2_result": dev2_result, "workdir": workdir}


def _write_hook_wrapper(workdir: str) -> str:
    wrapper_path = os.path.join(workdir, "session_end_wrapper.py")
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(
            "import json, sys, subprocess\n"
            "payload = json.load(sys.stdin)\n"
            "subprocess.run([\n"
            f"    {SM_BIN!r}, 'hook', 'session-end',\n"
            "    '--cwd', payload['cwd'],\n"
            "    '--session-id', payload['session_id'],\n"
            "    '--transcript-path', payload['transcript_path'],\n"
            "    '--assistant', 'claude-code',\n"
            "])\n"
        )
    return wrapper_path


def run_condition_t1(scenario: Scenario, workdir: str) -> dict:
    """
    Full session-memory framework, tested end-to-end with the real system:
    a real dev1 `claude -p` session establishes the decision, is captured
    and indexed via the real session-end hook (invoked explicitly here
    rather than relying on claude -p to wait for the hook, which was
    observed to time out), and dev2's fresh session has the real MCP
    server available.
    """
    os.makedirs(workdir, exist_ok=True)

    subprocess.run(
        [SM_BIN, "init", "--path", workdir, "--name", scenario.id],
        check=True, capture_output=True, text=True,
    )

    wrapper_path = _write_hook_wrapper(workdir)
    os.makedirs(os.path.join(workdir, ".claude"), exist_ok=True)
    with open(os.path.join(workdir, ".claude", "settings.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"hooks": {"SessionEnd": [{"hooks": [{"type": "command", "command": f"python3 {wrapper_path}"}]}]}},
            f,
        )

    mcp_config_path = os.path.join(workdir, ".mcp.json")
    with open(mcp_config_path, "w", encoding="utf-8") as f:
        json.dump({"mcpServers": {"session-memory": {"command": SM_BIN, "args": ["serve"]}}}, f)

    dev1_result = run_claude(scenario.dev1_prompt, cwd=workdir)

    transcript_path = _find_transcript_path(dev1_result["session_id"])
    capture = subprocess.run(
        [SM_BIN, "hook", "session-end", "--cwd", workdir, "--session-id", dev1_result["session_id"],
         "--transcript-path", transcript_path, "--assistant", "claude-code"],
        capture_output=True, text=True,
    )

    dev2_result = run_claude(scenario.dev2_task, cwd=workdir, mcp_config_path=mcp_config_path)
    return {
        "condition": "T1",
        "dev1_result": dev1_result,
        "capture_stdout": capture.stdout,
        "dev2_result": dev2_result,
        "workdir": workdir,
    }
