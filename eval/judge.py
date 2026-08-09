import json

from eval.claude_runner import run_claude
from eval.scenarios import Scenario

JUDGE_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "correct": {
            "type": "boolean",
            "description": "Does the response correctly reflect the established decision, per the gold criteria?",
        },
        "confabulated": {
            "type": "boolean",
            "description": "Does the response confidently state something specific and WRONG, as opposed to "
            "either being correct or honestly expressing uncertainty / lack of information?",
        },
        "reasoning": {"type": "string", "description": "One or two sentences explaining the verdict."},
    },
    "required": ["correct", "confabulated", "reasoning"],
})


def grade_response(scenario: Scenario, response_text: str, judge_workdir: str) -> dict:
    """
    Grades a dev2 response against the scenario's gold criteria using a
    fresh, isolated `claude -p` call as an LLM judge -- no project files, no
    memory system, no knowledge of which condition produced the response.
    `confabulated` specifically flags a confident, specific WRONG answer as
    distinct from an honest "I don't know", to test the paper's "graceful
    degradation... acknowledged uncertainty over confabulation" claim.
    """
    prompt = (
        "You are grading whether an AI coding assistant's response correctly reflects a "
        "previously-established project decision. Judge ONLY against the gold criteria below -- "
        "not your own opinion of what the 'best' general engineering answer would be. The point is "
        "whether the response reflects the SPECIFIC decision that was established, not whether it's "
        "reasonable engineering advice in the abstract.\n\n"
        f"TASK POSED TO THE ASSISTANT:\n{scenario.dev2_task}\n\n"
        f"GOLD CRITERIA (the established decision, and what a correct response must reflect):\n"
        f"{scenario.gold_answer_criteria}\n\n"
        f"THE ASSISTANT'S ACTUAL RESPONSE:\n{response_text}\n\n"
        "Return your verdict."
    )
    result = run_claude(prompt, cwd=judge_workdir, json_schema=JUDGE_SCHEMA)
    return _parse_verdict(result)


def _parse_verdict(result: dict) -> dict:
    raw = result.get("result", "")
    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError:
        return {"correct": None, "confabulated": None, "reasoning": f"UNPARSEABLE JUDGE OUTPUT: {raw[:500]}"}
    return {
        "correct": verdict.get("correct"),
        "confabulated": verdict.get("confabulated"),
        "reasoning": verdict.get("reasoning"),
    }
