"""Editorial ordering: diversity quotas from recent publishes + fallback interleaving."""

from __future__ import annotations

import os
import time
from collections import Counter, defaultdict
from typing import Iterable

from workers.dedupe import RecentPublishRow
from workers.planner import PlannedTopic


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _norm_game(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


# Substring -> series bucket for daily caps (matches planner game families where useful)
_SERIES_FROM_GAME: list[tuple[str, str]] = [
    ("gta", "gta"),
    ("skyrim", "tes"),
    ("oblivion", "tes"),
    ("morrowind", "tes"),
    ("elder scrolls", "tes"),
    ("cyberpunk", "cyberpunk"),
    ("resident evil", "resident_evil"),
    ("pes ", "sports_career"),
    ("fifa", "sports_career"),
    ("fc 2", "sports_career"),
    ("fc 24", "sports_career"),
    ("mount", "mount_blade"),
    ("bannerlord", "mount_blade"),
    ("warband", "mount_blade"),
    ("red dead", "rdr"),
    ("fallout", "fallout"),
    ("witcher", "witcher"),
    ("silent hill", "silent_hill"),
    ("minecraft", "minecraft"),
    ("the sims", "sims"),
    ("sims ", "sims"),
]


def series_bucket_for_game(game: str, explicit_series: str | None) -> str:
    if explicit_series and explicit_series.strip():
        return explicit_series.strip().lower()
    g = game.lower()
    for needle, bucket in _SERIES_FROM_GAME:
        if needle in g:
            return bucket
    return f"game:{_norm_game(game)}"


def _utc_day_bucket(ts: int) -> int:
    return ts // 86400


def _underrepresented(
    topic: PlannedTopic,
    lookback_start: int,
    rows: Iterable[RecentPublishRow],
) -> tuple[bool, bool]:
    """(game_missing, content_type_missing) in lookback window."""
    games: set[str] = set()
    cts: set[str] = set()
    for r in rows:
        if r.published_at < lookback_start:
            continue
        if r.game_name:
            games.add(_norm_game(r.game_name))
        if r.content_type:
            cts.add(r.content_type.strip().lower())
    g_miss = _norm_game(topic.game) not in games
    ct_miss = topic.content_type.strip().lower() not in cts
    return g_miss, ct_miss


def _violation_score(
    topic: PlannedTopic,
    today_game: Counter[str],
    today_ct: Counter[str],
    today_series: Counter[str],
    max_game: int,
    max_ct: int,
    max_series: int,
) -> int:
    g = _norm_game(topic.game)
    sk = series_bucket_for_game(topic.game, topic.series)
    v = 0
    if max_game > 0 and today_game[g] >= max_game:
        v += 1
    if max_ct > 0 and today_ct[topic.content_type.strip().lower()] >= max_ct:
        v += 1
    if max_series > 0 and today_series[sk] >= max_series:
        v += 1
    return v


def _fallback_interleave(topics: list[PlannedTopic], day_bucket: int) -> list[PlannedTopic]:
    """Spread content types when there is no DB history (deterministic by UTC day)."""
    buckets: dict[str, list[PlannedTopic]] = defaultdict(list)
    for t in topics:
        buckets[t.content_type].append(t)
    for k, items in list(buckets.items()):
        items.sort(key=lambda x: (-x.priority, x.source_topic_key))
        if items:
            off = day_bucket % len(items)
            buckets[k] = items[off:] + items[:off]
    type_order = ["list", "tech", "guide", "cheats", "article"]
    types = [c for c in type_order if buckets.get(c)]
    types.extend(sorted(c for c in buckets if c not in types))
    if not types:
        return list(topics)
    out: list[PlannedTopic] = []
    while any(buckets[t] for t in buckets):
        for ct in types:
            if buckets.get(ct):
                out.append(buckets[ct].pop(0))
    return out


def select_next_topics(
    topics: list[PlannedTopic],
    recent_rows: list[RecentPublishRow],
    *,
    now_ts: int | None = None,
) -> list[PlannedTopic]:
    """
    Re-order planned topics: respect per-day caps from recent DB rows, boost underrepresented
    game/content_type in lookback window; without data, interleave by content_type.
    """
    if not topics:
        return []
    flag = os.environ.get("DIVERSITY_PLANNING", "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return list(topics)

    now_ts = now_ts or int(time.time())
    day_bucket = _utc_day_bucket(now_ts)
    today_start_ts = day_bucket * 86400

    if not recent_rows:
        return _fallback_interleave(topics, day_bucket)

    max_game = _env_int("DIVERSITY_MAX_PER_GAME_PER_DAY", 1)
    max_ct = _env_int("DIVERSITY_MAX_PER_CONTENT_TYPE_PER_DAY", 2)
    max_series = _env_int("DIVERSITY_MAX_PER_SERIES_PER_DAY", 2)
    lookback_days = _env_int("DIVERSITY_LOOKBACK_DAYS", 7)
    lookback_start = now_ts - max(1, lookback_days) * 86400

    today_game: Counter[str] = Counter()
    today_ct: Counter[str] = Counter()
    today_series: Counter[str] = Counter()
    for r in recent_rows:
        if r.published_at < today_start_ts:
            continue
        if r.game_name:
            today_game[_norm_game(r.game_name)] += 1
        if r.content_type:
            today_ct[r.content_type.strip().lower()] += 1
        if r.game_name:
            today_series[series_bucket_for_game(r.game_name, None)] += 1

    bonus_game = _env_int("DIVERSITY_UNDERREP_GAME_BONUS", 100)
    bonus_ct = _env_int("DIVERSITY_UNDERREP_TYPE_BONUS", 40)

    scored: list[tuple[tuple[int, int, int, str], PlannedTopic]] = []
    for t in topics:
        v = _violation_score(t, today_game, today_ct, today_series, max_game, max_ct, max_series)
        g_miss, ct_miss = _underrepresented(t, lookback_start, recent_rows)
        rep = 0
        if g_miss:
            rep += bonus_game
        if ct_miss:
            rep += bonus_ct
        # Lower violation count first, higher rep, higher priority, stable key
        key = (v, -rep, -t.priority, t.source_topic_key)
        scored.append((key, t))

    scored.sort(key=lambda x: x[0])
    return [x[1] for x in scored]
