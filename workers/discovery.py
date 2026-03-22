"""Load topic candidates from static YAML (no LLM)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RawCandidate:
    game: str
    template_key: str
    priority: int
    forum_slug: str | None
    enabled: bool


def _workers_dir() -> Path:
    return Path(__file__).resolve().parent


def default_candidates_path() -> Path:
    override = os.environ.get("TOPIC_CANDIDATES_PATH")
    if override:
        return Path(override)
    return _workers_dir() / "data" / "topic_candidates.yaml"


def load_candidates(path: Path | None = None) -> tuple[dict[str, Any], list[RawCandidate]]:
    p = path or default_candidates_path()
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not raw or "candidates" not in raw:
        raise ValueError(f"Invalid candidates file: {p}")

    templates = raw.get("templates") or {}
    out: list[RawCandidate] = []
    for row in raw["candidates"]:
        if not row.get("enabled", True):
            continue
        out.append(
            RawCandidate(
                game=str(row["game"]).strip(),
                template_key=str(row["template_key"]).strip(),
                priority=int(row.get("priority", 0)),
                forum_slug=(str(row["forum_slug"]).strip() if row.get("forum_slug") else None),
                enabled=True,
            )
        )
    return templates, out
