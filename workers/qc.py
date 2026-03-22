"""Rule-based quality gate before publish."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

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

    return QCResult(True, "ok")
