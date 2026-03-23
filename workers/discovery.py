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
    series: str | None = None


def _workers_dir() -> Path:
    return Path(__file__).resolve().parent


def default_candidates_path() -> Path:
    override = os.environ.get("TOPIC_CANDIDATES_PATH")
    if override:
        return Path(override)
    return _workers_dir() / "data" / "topic_candidates.yaml"


def default_content_matrix_path() -> Path:
    override = os.environ.get("CONTENT_MATRIX_PATH")
    if override:
        return Path(override)
    return _workers_dir() / "data" / "content_matrix.yaml"


def load_content_matrix(path: Path | None = None) -> dict[str, list[str]]:
    """game title -> allowed template_key list. Missing games = no restriction."""
    p = path or default_content_matrix_path()
    if not p.exists():
        return {}
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not doc:
        return {}
    m = doc.get("matrix") if isinstance(doc, dict) else None
    if m is None and isinstance(doc, dict):
        m = doc
    if not isinstance(m, dict):
        return {}
    out: dict[str, list[str]] = {}
    for game, templates in m.items():
        if not isinstance(templates, list):
            continue
        out[str(game).strip()] = [str(x).strip() for x in templates if str(x).strip()]
    return out


def _filter_by_matrix(
    candidates: list[RawCandidate],
    matrix: dict[str, list[str]],
) -> list[RawCandidate]:
    if not matrix:
        return candidates
    kept: list[RawCandidate] = []
    for c in candidates:
        allowed = matrix.get(c.game)
        if allowed is None:
            kept.append(c)
        elif c.template_key in allowed:
            kept.append(c)
    return kept


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
        series_val = row.get("series")
        out.append(
            RawCandidate(
                game=str(row["game"]).strip(),
                template_key=str(row["template_key"]).strip(),
                priority=int(row.get("priority", 0)),
                forum_slug=(str(row["forum_slug"]).strip() if row.get("forum_slug") else None),
                enabled=True,
                series=(str(series_val).strip() if series_val else None),
            )
        )
    matrix = load_content_matrix()
    out = _filter_by_matrix(out, matrix)
    return templates, out
