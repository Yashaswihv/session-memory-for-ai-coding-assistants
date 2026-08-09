import json
import os


def load_json(path: str) -> dict:
    """Loads a JSON config file, defaulting to {} if it doesn't exist yet.
    Refuses to silently clobber a file that exists but isn't valid JSON --
    surfaces that as an error instead of overwriting whatever the user (or
    another tool) put there."""
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"{path} exists but isn't valid JSON ({e}) -- refusing to touch it. "
            f"Fix or remove it manually, then re-run."
        )


def save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
