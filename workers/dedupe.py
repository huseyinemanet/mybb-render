"""Pre-filter against known source_topic_key / canonical_intent (optional PostgreSQL)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

from workers.planner import PlannedTopic


def normalize_intent(s: str) -> str:
    """Match MyBB mybb_normalize_intent (approx): lower, collapse space, max 250."""
    t = " ".join(str(s).strip().lower().split())
    return t[:250]


@dataclass
class DedupeState:
    source_keys: set[str]
    intents: set[str]
    slug_to_fid: dict[str, int]


@dataclass(frozen=True)
class RecentPublishRow:
    """Rows from content_meta for editorial diversity (game_name, content_type, published_at)."""

    game_name: str
    content_type: str
    published_at: int


def _table(prefix: str, name: str) -> str:
    p = prefix.rstrip("_") + "_" if prefix and not prefix.endswith("_") else prefix
    if not p.endswith("_"):
        p += "_"
    full = f"{p}{name}"
    if not re.match(r"^[a-zA-Z0-9_]+$", full):
        raise ValueError(f"unsafe table name: {full!r}")
    return full


def _connect_dsn() -> str | None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    host = os.environ.get("MYBB_DB_HOST", "").strip()
    name = os.environ.get("MYBB_DB_NAME", "").strip()
    user = os.environ.get("MYBB_DB_USER", "").strip()
    password = os.environ.get("MYBB_DB_PASSWORD", "").strip()
    port = os.environ.get("MYBB_DB_PORT", "5432").strip()
    if not (host and name and user):
        return None
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def load_dedupe_state() -> DedupeState | None:
    dsn = _connect_dsn()
    if not dsn:
        return None
    prefix = os.environ.get("MYBB_TABLE_PREFIX", "mybb_")
    try:
        import psycopg
    except ImportError:
        return None

    keys: set[str] = set()
    intents: set[str] = set()
    slug_to_fid: dict[str, int] = {}
    t_meta = _table(prefix, "content_meta")
    t_intent = _table(prefix, "thread_intent_index")
    t_map = _table(prefix, "forum_seed_map")
    with psycopg.connect(dsn, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(f'SELECT source_topic_key FROM "{t_meta}"')
                for (k,) in cur.fetchall():
                    if k:
                        keys.add(str(k))
            except Exception:
                pass
            try:
                cur.execute(f'SELECT normalized_intent FROM "{t_intent}"')
                for (k,) in cur.fetchall():
                    if k:
                        intents.add(str(k))
            except Exception:
                pass
            try:
                cur.execute(f'SELECT slug, fid FROM "{t_map}"')
                for slug, fid in cur.fetchall():
                    if slug and fid is not None:
                        slug_to_fid[str(slug)] = int(fid)
            except Exception:
                pass
    return DedupeState(keys, intents, slug_to_fid)


def load_recent_content_meta(
    lookback_days: int | None = None,
) -> list[RecentPublishRow]:
    """
    Fetch recent publishes for diversity quotas. Returns [] if no DB or table missing.
    lookback_days from DIVERSITY_QUERY_LOOKBACK_DAYS (default 45).
    """
    dsn = _connect_dsn()
    if not dsn:
        return []
    if lookback_days is None:
        raw = os.environ.get("DIVERSITY_QUERY_LOOKBACK_DAYS", "").strip()
        lookback_days = int(raw) if raw.isdigit() else 45
    lookback_days = max(1, min(lookback_days, 365))
    prefix = os.environ.get("MYBB_TABLE_PREFIX", "mybb_")
    try:
        import psycopg
    except ImportError:
        return []

    t_meta = _table(prefix, "content_meta")
    import time

    cutoff = int(time.time()) - lookback_days * 86400
    out: list[RecentPublishRow] = []
    try:
        with psycopg.connect(dsn, connect_timeout=15) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT game_name, content_type, published_at
                    FROM "{t_meta}"
                    WHERE published_at >= %s
                    ORDER BY published_at DESC
                    """,
                    (cutoff,),
                )
                for game_name, content_type, published_at in cur.fetchall():
                    g = str(game_name or "").strip()
                    ct = str(content_type or "").strip()
                    try:
                        ts = int(published_at)
                    except (TypeError, ValueError):
                        continue
                    out.append(RecentPublishRow(g, ct, ts))
    except Exception:
        return []
    return out


def fetch_slug_to_fid_http(base_url: str, secret: str) -> dict[str, int]:
    """
    GET forum_map_bridge.php (same auth as publish_bridge).
    Used when DATABASE_URL is not available (e.g. GitHub Actions).
    """
    url = base_url.rstrip("/") + "/forum_map_bridge.php"
    headers = {"X-MyBB-Publish-Secret": secret}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.get(url, headers=headers)
        data: dict[str, Any] = r.json()
    except Exception:
        return {}
    if not data.get("ok") or not isinstance(data.get("slug_to_fid"), dict):
        return {}
    out: dict[str, int] = {}
    for k, v in data["slug_to_fid"].items():
        try:
            out[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def filter_planned(
    topics: list[PlannedTopic],
    state: DedupeState | None,
) -> tuple[list[PlannedTopic], list[str]]:
    """Return (kept, log_lines)."""
    if not state:
        return topics, ["dedupe: no state"]
    if not state.source_keys and not state.intents:
        return topics, ["dedupe: no DB prefetch; duplicate check at publish_bridge only"]
    kept: list[PlannedTopic] = []
    log: list[str] = []
    for t in topics:
        if t.source_topic_key in state.source_keys:
            log.append(f"skip source_key exists: {t.source_topic_key}")
            continue
        ni = normalize_intent(t.canonical_intent)
        if ni in state.intents:
            log.append(f"skip intent exists: {ni[:80]}...")
            continue
        kept.append(t)
    return kept, log


def resolve_fid(planned: PlannedTopic, state: DedupeState | None) -> int | None:
    if state and planned.forum_slug in state.slug_to_fid:
        return state.slug_to_fid[planned.forum_slug]
    raw = os.environ.get("WORKER_FORUM_FIDS_JSON", "").strip()
    if raw:
        try:
            import json

            m = json.loads(raw)
            v = m.get(planned.forum_slug)
            return int(v) if v is not None else None
        except Exception:
            return None
    return None
