"""Map candidates to forum slugs, thread title, source_topic_key, canonical_intent."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from workers.discovery import RawCandidate


def _slugify_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-+", "-", s)[:120]


@dataclass
class PlannedTopic:
    game: str
    template_key: str
    content_type: str
    forum_slug: str
    subject: str
    source_topic_key: str
    canonical_intent: str
    priority: int
    safe_tier: str


# Game name substring -> default popular-forum slug (MVP routing)
_GAME_FAMILY_FORUM: list[tuple[str, str]] = [
    ("gta", "forum_pop_gta"),
    ("skyrim", "forum_pop_tes"),
    ("oblivion", "forum_pop_tes"),
    ("morrowind", "forum_pop_tes"),
    ("elder scrolls", "forum_pop_tes"),
    ("cyberpunk", "forum_pop_cyberpunk"),
    ("resident evil", "forum_pop_re"),
    ("pes ", "forum_pop_pes_fifa"),
    ("fifa", "forum_pop_pes_fifa"),
    ("fc 2", "forum_pop_pes_fifa"),
    ("mount", "forum_pop_mb"),
    ("bannerlord", "forum_pop_mb"),
    ("warband", "forum_pop_mb"),
    ("red dead", "forum_pop_rdr"),
    ("fallout", "forum_pop_fallout"),
    ("witcher", "forum_pop_witcher"),
    ("silent hill", "forum_pop_sh"),
    ("minecraft", "forum_pop_minecraft"),
    ("the sims", "forum_pop_sims"),
    ("sims ", "forum_pop_sims"),
]


def _default_forum_for_game(game: str) -> str:
    g = game.lower()
    for needle, slug in _GAME_FAMILY_FORUM:
        if needle in g:
            return slug
    return "forum_lists_story"


def _template_subject_and_intent(
    game: str, template_key: str, tpl: dict[str, Any]
) -> tuple[str, str]:
    """Return (subject, canonical_intent) — intent is stable for dedupe."""
    patterns: dict[str, tuple[str, str]] = {
        "cheats_full_list": (
            f"{game} hileleri tam liste (tek oyunculu)",
            f"{game} tek oyunculu hile ve kod listesi özeti",
        ),
        "save_location": (
            f"{game} save dosyası nerede (PC)",
            f"{game} kayıt dosyası konumu ve yedekleme",
        ),
        "fps_tweaks": (
            f"{game} FPS artırma ve performans ayarları",
            f"{game} düşük fps ve grafik optimizasyonu",
        ),
        "quest_guide_stub": (
            f"{game} görev rehberi — giriş",
            f"{game} ana görev ve ilerleme rehberi giriş",
        ),
        "puzzle_stub": (
            f"{game} bulmaca ve bölüm çözümü — giriş",
            f"{game} puzzle ve bölüm çözüm rehberi giriş",
        ),
        "career_youth": (
            f"{game} kariyer modu genç oyuncular — özet",
            f"{game} kariyer modu genç yetenek listesi özeti",
        ),
        "lowspec_list": (
            "Düşük sistem için oyun önerileri — ek liste",
            "düşük donanım için tek oyunculu oyun önerileri",
        ),
    }
    if template_key in patterns:
        return patterns[template_key]
    subj = tpl.get("default_subject") or f"{game} — {template_key}"
    intent = tpl.get("default_intent") or _slugify_key(f"{game}-{template_key}").replace("-", " ")
    return str(subj), str(intent)


def plan_topics(
    templates: dict[str, Any],
    raw: list[RawCandidate],
    max_candidates: int | None = None,
) -> list[PlannedTopic]:
    planned: list[PlannedTopic] = []
    for c in raw:
        tpl = templates.get(c.template_key) or {}
        content_type = str(tpl.get("content_type") or "article")
        safe_tier = str(tpl.get("safe_tier") or "low")
        forum_slug = c.forum_slug or str(tpl.get("forum_slug") or "")
        if not forum_slug:
            forum_slug = _default_forum_for_game(c.game)

        subject, canonical_intent = _template_subject_and_intent(c.game, c.template_key, tpl)
        source_topic_key = _slugify_key(f"auto-{c.template_key}-{c.game}")

        planned.append(
            PlannedTopic(
                game=c.game,
                template_key=c.template_key,
                content_type=content_type,
                forum_slug=forum_slug,
                subject=subject,
                source_topic_key=source_topic_key,
                canonical_intent=canonical_intent,
                priority=c.priority,
                safe_tier=safe_tier,
            )
        )

    planned.sort(key=lambda x: (-x.priority, x.source_topic_key))
    if max_candidates is not None:
        planned = planned[: max(0, max_candidates)]
    return planned
