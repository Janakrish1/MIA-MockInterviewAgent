"""Persist interview turn feedback for report generation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STORE_DIR = Path(__file__).resolve().parents[2] / "documents" / "interview_feedback"


def append_feedback(interview_id: str, entry: dict[str, Any]) -> Path:
    """Append a single scored turn to a session-scoped JSONL file."""
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    target = STORE_DIR / f"{interview_id}.jsonl"
    enriched = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(enriched, ensure_ascii=True) + "\n")
    return target


def read_feedback(interview_id: str) -> list[dict[str, Any]]:
    """Read all stored feedback entries for an interview session."""
    target = STORE_DIR / f"{interview_id}.jsonl"
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows
