"""Rule-based quality gate before publish."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from workers.planner import PlannedTopic


@dataclass
class QCResult:
    ok: bool
    reason: str


_BANNED_SUBSTR = [
    "online hile",
    "multiplayer cheat",
    "multiplayer hile",
    "pvp exploit",
    "dupe glitch online",
    "korsan indir",
    "crack indir",
    "hile multiplayer",
    "anticheat bypass",
]


def _min_body_len() -> int:
    return max(80, int(os.environ.get("QC_MIN_BODY_LEN", "200")))


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _cheats_min_entries() -> int:
    return max(1, _env_int("CHEATS_MIN_ENTRIES", 5))


def _cheats_max_entries() -> int:
    return max(_cheats_min_entries(), _env_int("CHEATS_MAX_ENTRIES", 15))


def _links_min_items() -> int:
    return max(0, _env_int("QC_INTERNAL_LINK_HINTS_MIN", 2))


def _links_max_items() -> int:
    return max(_links_min_items(), _env_int("QC_INTERNAL_LINK_HINTS_MAX", 3))


_CHEAT_CODE_VALID = re.compile(r"^[A-Z0-9_ ]{3,24}$")


def _max_repeat_sentence_ratio(text: str) -> float:
    sents = re.split(r"[.!?]+\s+", text)
    sents = [s.strip().lower() for s in sents if len(s.strip()) > 20]
    if len(sents) < 3:
        return 0.0
    uniq = len(set(sents))
    return 1.0 - (uniq / len(sents))


def check_topic(
    topic: PlannedTopic,
    subject: str,
    body: str,
    raw_art: dict[str, Any] | None = None,
) -> QCResult:
    # Only auto-publish low/medium; mark templates as high to force manual later.
    if topic.safe_tier not in ("low", "medium"):
        return QCResult(
            False,
            f"safe_tier={topic.safe_tier!r} not auto-published (use low or medium)",
        )

    combined = f"{subject}\n{body}".lower()
    for b in _BANNED_SUBSTR:
        if b in combined:
            return QCResult(False, f"banned phrase: {b}")

    game_l = topic.game.lower()
    if game_l and game_l not in combined and topic.game.split()[0].lower() not in combined:
        return QCResult(False, "game name not reflected in subject/body")

    if len(body.strip()) < _min_body_len():
        return QCResult(False, f"body too short (< {_min_body_len()})")

    if _max_repeat_sentence_ratio(body) > 0.45:
        return QCResult(False, "too many repeated sentences")

    raw = raw_art if isinstance(raw_art, dict) else {}
    hints = raw.get("internal_link_hints")
    if not isinstance(hints, list):
        return QCResult(False, "internal_link_hints must be a list in raw article")
    hints_count = len([h for h in hints if str(h).strip()])
    if hints_count < _links_min_items() or hints_count > _links_max_items():
        return QCResult(False, f"internal_link_hints count must be {_links_min_items()}-{_links_max_items()}")

    cheats = raw.get("cheat_entries")
    if topic.content_type == "cheats":
        if not isinstance(cheats, list):
            return QCResult(False, "cheat_entries must be a list for cheats content")
        count = len(cheats)
        if count < _cheats_min_entries() or count > _cheats_max_entries():
            return QCResult(False, f"cheat_entries count must be {_cheats_min_entries()}-{_cheats_max_entries()}")
        for i, row in enumerate(cheats, start=1):
            if not isinstance(row, dict):
                return QCResult(False, f"cheat_entries[{i}] must be object")
            code = str(row.get("code", "")).strip()
            effect = str(row.get("effect", "")).strip()
            note = str(row.get("platform_note", "")).strip()
            confidence = str(row.get("confidence", "")).strip().lower()
            if confidence != "high":
                return QCResult(False, f"cheat_entries[{i}] confidence must be high")
            if not _CHEAT_CODE_VALID.match(code):
                return QCResult(False, f"cheat_entries[{i}] invalid code format")
            if len(effect) < 3 or len(effect) > 140:
                return QCResult(False, f"cheat_entries[{i}] invalid effect length")
            if len(note) > 120:
                return QCResult(False, f"cheat_entries[{i}] platform_note too long")
    else:
        if isinstance(cheats, list) and len(cheats) > 0:
            return QCResult(False, "cheat_entries must be empty for non-cheats content")

    return QCResult(True, "ok")
