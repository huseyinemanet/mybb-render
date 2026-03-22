#!/usr/bin/env python3
"""
Content pipeline entrypoint: discovery → plan → dedupe → generate → QC → publish.

Run from repository root:
  pip install -r workers/requirements.txt
  export MYBB_BASE_URL=... MYBB_PUBLISH_SECRET=... OPENAI_API_KEY=...
  python -m workers.pipeline

Optional: DATABASE_URL or MYBB_DB_* + MYBB_TABLE_PREFIX for pre-dedupe and forum fid map.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback

from workers.dedupe import (
    DedupeState,
    fetch_slug_to_fid_http,
    filter_planned,
    load_dedupe_state,
    resolve_fid,
)
from workers.discovery import load_candidates
from workers.generate import generate_for_topic
from workers.llm_client import resolve_llm_provider
from workers.planner import plan_topics
from workers.publish import publish_thread
from workers.qc import check_topic

LOG = logging.getLogger("mybb_worker")


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _setup_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )


def main() -> int:
    _setup_logging()
    dry = os.environ.get("DRY_RUN", "").strip().lower() in ("1", "true", "yes")
    max_pub = max(0, _env_int("MAX_PUBLISH_PER_RUN", 1))
    max_pool = _env_int("MAX_CANDIDATES_PLAN", 25)
    if dry:
        max_pub = max(1, min(max_pub, _env_int("MAX_DRY_PREVIEW", 1)))

    base = os.environ.get("MYBB_BASE_URL", "").rstrip("/")
    secret = os.environ.get("MYBB_PUBLISH_SECRET", "").strip()
    if not dry and (not base or not secret):
        LOG.error("MYBB_BASE_URL and MYBB_PUBLISH_SECRET required (or set DRY_RUN=1)")
        return 2

    skip_llm = os.environ.get("SKIP_LLM", "").strip().lower() in ("1", "true", "yes")
    if (
        not dry
        and not skip_llm
        and not os.environ.get("OPENAI_API_KEY")
        and not os.environ.get("ANTHROPIC_API_KEY")
    ):
        LOG.error("Set OPENAI_API_KEY or ANTHROPIC_API_KEY (or SKIP_LLM=1 for smoke test)")
        return 2

    if not dry and not skip_llm:
        LOG.info("llm_provider=%s", resolve_llm_provider())

    templates, raw = load_candidates()
    planned = plan_topics(templates, raw, max_candidates=max_pool)
    LOG.info("planned_candidates=%s", len(planned))

    state: DedupeState | None = load_dedupe_state()
    if state is None:
        state = DedupeState(set(), set(), {})
    else:
        LOG.info(
            "db_prefetch keys=%s intents=%s forums=%s",
            len(state.source_keys),
            len(state.intents),
            len(state.slug_to_fid),
        )

    if not state.slug_to_fid and base and secret:
        http_map = fetch_slug_to_fid_http(base, secret)
        if http_map:
            state.slug_to_fid.update(http_map)
            LOG.info("forum_map_bridge slugs=%s", len(http_map))
        else:
            LOG.warning("forum_map_bridge empty or failed (deploy forum_map_bridge.php + MYBB_PUBLISH_SECRET)")

    kept, dlog = filter_planned(planned, state)
    for line in dlog:
        LOG.info("dedupe %s", line)
    LOG.info("after_dedupe=%s", len(kept))

    published = 0
    for topic in kept:
        if published >= max_pub:
            LOG.info("MAX_PUBLISH_PER_RUN reached (%s)", max_pub)
            break

        fid = resolve_fid(topic, state)
        if fid is None or fid <= 0:
            LOG.warning("skip no fid for slug=%s (set DATABASE_URL or WORKER_FORUM_FIDS_JSON)", topic.forum_slug)
            continue

        try:
            if skip_llm:
                subject = topic.subject
                body = (
                    f"[b]Otomasyon test — {topic.game}[/b]\n\n"
                    f"Bu paragraf {topic.template_key} şablonu için yer tutucudur. "
                    f"Platform ve sürüm bilgisini yorumlarda paylaşın.\n\n"
                    f"İkinci paragraf: yalnızca tek oyunculu içerik; çevrimiçi hile önerilmez.\n\n"
                    "[list]\n"
                    "[*]Kaynağı doğrulayın\n"
                    "[*]Kayıt dosyalarını yedekleyin\n"
                    "[*]Resmi yama notlarını kontrol edin\n"
                    "[/list]"
                )
                raw_art = {}
            else:
                subject, body, raw_art = generate_for_topic(topic)
        except Exception as e:
            LOG.error("generate failed %s: %s", topic.source_topic_key, e)
            LOG.debug(traceback.format_exc())
            continue

        qc = check_topic(topic, subject, body)
        if not qc.ok:
            LOG.warning("qc_reject %s: %s", topic.source_topic_key, qc.reason)
            continue

        if dry:
            LOG.info(
                "dry_run would publish fid=%s key=%s subject=%s",
                fid,
                topic.source_topic_key,
                subject[:80],
            )
            LOG.debug("body_preview=%s", body[:400])
            published += 1
            continue

        res = publish_thread(base, secret, fid, topic, subject, body)
        status = res.get("_http_status")
        if res.get("ok") is True:
            LOG.info("published tid=%s key=%s", res.get("tid"), topic.source_topic_key)
            published += 1
            state.source_keys.add(topic.source_topic_key)
            from workers.dedupe import normalize_intent

            state.intents.add(normalize_intent(topic.canonical_intent))
        elif res.get("error") in ("duplicate_intent", "duplicate_source_key"):
            LOG.info("bridge_duplicate %s %s", topic.source_topic_key, res.get("error"))
        else:
            LOG.error("publish_fail %s status=%s body=%s", topic.source_topic_key, status, json.dumps(res)[:500])

    LOG.info("done published=%s dry_run=%s", published, dry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
