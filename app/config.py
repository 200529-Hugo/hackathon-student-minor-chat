import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def minors_path() -> Path:
    configured = Path(os.getenv("MINORS_FILE", "data/minors.json"))
    path = configured if configured.is_absolute() else ROOT / configured
    return path if path.exists() else ROOT / "data/sample_minors.json"
