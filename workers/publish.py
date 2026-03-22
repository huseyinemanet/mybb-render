"""POST to publish_bridge.php."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from workers.planner import PlannedTopic


def publish_thread(
    base_url: str,
    secret: str,
    fid: int,
    topic: PlannedTopic,
    subject: str,
    message: str,
    uid: int | None = None,
    quality_score: float = 0.75,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/publish_bridge.php"
    if uid is None:
        raw = (os.environ.get("MYBB_PUBLISH_UID") or "").strip()
        uid = int(raw) if raw else 1
    payload = {
        "fid": fid,
        "subject": subject,
        "message": message,
        "uid": uid,
        "source_topic_key": topic.source_topic_key,
        "canonical_intent": topic.canonical_intent,
        "game_name": topic.game,
        "content_type": topic.content_type,
        "quality_score": quality_score,
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-MyBB-Publish-Secret": secret,
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, headers=headers, content=json.dumps(payload, ensure_ascii=False))
    try:
        data = r.json()
    except Exception:
        data = {"error": "non_json", "text": r.text[:500]}
    data["_http_status"] = r.status_code
    return data
