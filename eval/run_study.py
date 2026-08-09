"""
Treatment/control study: for each scenario, runs dev2's task under three
conditions (C0: no memory, C1: static AGENTS.md, T1: full session-memory
framework), grades each response with an LLM judge, and saves raw + summary
results. Uses `claude -p` throughout -- no separate API key needed.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conditions import run_condition_c0, run_condition_c1, run_condition_t1  # noqa: E402
from judge import grade_response  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def _isolate_registry():
    """Ensures this study never touches the developer's real global
    registry -- every subprocess spawned from here (including nested
    `claude -p` -> `session-memory serve` chains) inherits this env var."""
    isolated_dir = tempfile.mkdtemp(prefix="session_memory_eval_registry_")
    os.environ["SESSION_MEMORY_REGISTRY_DIR"] = isolated_dir
    return isolated_dir


def run_scenario(scenario, base_dir: str, judge_dir: str) -> dict:
    scenario_dir = os.path.join(base_dir, scenario.id)
    record = {"scenario_id": scenario.id, "category": scenario.category, "conditions": {}}

    for condition_name, run_fn in (("C0", run_condition_c0), ("C1", run_condition_c1), ("T1", run_condition_t1)):
        workdir = os.path.join(scenario_dir, condition_name.lower())
        try:
            outcome = run_fn(scenario, workdir)
            response_text = outcome["dev2_result"]["result"]
            verdict = grade_response(scenario, response_text, judge_dir)
            record["conditions"][condition_name] = {
                "response": response_text,
                "cost_usd": outcome["dev2_result"].get("total_cost_usd"),
                "verdict": verdict,
            }
        except Exception as e:
            record["conditions"][condition_name] = {
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
    return record


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    isolated_registry = _isolate_registry()
    print(f"Isolated registry dir for this run: {isolated_registry}")

    run_root = tempfile.mkdtemp(prefix="session_memory_eval_run_")
    judge_dir = os.path.join(run_root, "_judge")
    os.makedirs(judge_dir, exist_ok=True)
    print(f"Scratch root for this run: {run_root}")

    limit = int(os.environ.get("SESSION_MEMORY_EVAL_LIMIT", "0")) or None
    scenarios = SCENARIOS[:limit] if limit else SCENARIOS

    results = []
    for i, scenario in enumerate(scenarios, start=1):
        print(f"\n[{i}/{len(scenarios)}] Running scenario: {scenario.id} ({scenario.category})")
        start = time.time()
        record = run_scenario(scenario, run_root, judge_dir)
        elapsed = time.time() - start
        record["elapsed_seconds"] = round(elapsed, 1)
        for cond, data in record["conditions"].items():
            if "error" in data:
                print(f"  {cond}: ERROR -- {data['error']}")
            else:
                v = data["verdict"]
                print(f"  {cond}: correct={v['correct']} confabulated={v['confabulated']}")
        results.append(record)

        # persist incrementally so a crash partway through doesn't lose progress
        with open(os.path.join(RESULTS_DIR, "study_results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    print(f"\nDone. Raw results at {os.path.join(RESULTS_DIR, 'study_results.json')}")
    print(f"Scratch data left at {run_root} (not auto-deleted -- inspect before cleanup)")

    shutil.rmtree(isolated_registry, ignore_errors=True)


if __name__ == "__main__":
    main()
