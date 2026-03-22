"""Build LLM prompt from PlannedTopic; parse JSON; render MyBB MyCode."""

from __future__ import annotations

from typing import Any

from workers.llm_client import generate_article
from workers.planner import PlannedTopic


def build_user_prompt(topic: PlannedTopic) -> str:
    return f"""Aşağıdaki konu için forum gönderisi üret.

Oyun: {topic.game}
İçerik tipi: {topic.content_type}
Şablon: {topic.template_key}
Hedef konu başlığı (thread subject): {topic.subject}
Niyet özeti (canonical): {topic.canonical_intent}

JSON alanları:
- title: thread başlığı (subject ile uyumlu, yıl ekleyebilirsin)
- intro: 2-4 cümle giriş [b]kalın[/b] ve normal metin karışık MyCode ile uyumlu düz metin (şimdilik düz metin üret, ben MyCode ekleyeceğim)
- sections: en az 2 bölüm; her bölümde heading, paragraphs (1-3 kısa paragraf), bullets (2-5 madde veya boş dizi)
- warnings: 1-3 uyarı (tek oyunculu, sürüm farkı, yedek al vb.)
- internal_link_hints: forumda açılabilecek ilgili konu başlığı önerileri (sadece metin, 0-3 öğe)

Metinde şunları yapma: çok oyunculu hile, cheat engine ile online, korsan bağlantı, politika ihlali.
"""


def article_to_mycode(data: dict[str, Any]) -> str:
    lines: list[str] = []
    intro = str(data.get("intro", "")).strip()
    if intro:
        lines.append(intro)
        lines.append("")

    for sec in data.get("sections") or []:
        h = str(sec.get("heading", "")).strip()
        if h:
            lines.append(f"[b]{h}[/b]")
            lines.append("")
        for p in sec.get("paragraphs") or []:
            p = str(p).strip()
            if p:
                lines.append(p)
                lines.append("")
        bullets = sec.get("bullets") or []
        if bullets:
            lines.append("[list]")
            for b in bullets:
                b = str(b).strip()
                if b:
                    lines.append(f"[*]{b}")
            lines.append("[/list]")
            lines.append("")

    warns = data.get("warnings") or []
    if warns:
        lines.append("[b]Uyarılar[/b]")
        lines.append("[list]")
        for w in warns:
            w = str(w).strip()
            if w:
                lines.append(f"[*]{w}")
        lines.append("[/list]")
        lines.append("")

    hints = data.get("internal_link_hints") or []
    if hints:
        lines.append("[b]İlgili konular[/b]")
        lines.append("[list]")
        for h in hints:
            h = str(h).strip()
            if h:
                lines.append(f"[*]{h}")
        lines.append("[/list]")

    return "\n".join(lines).strip()


def generate_for_topic(topic: PlannedTopic) -> tuple[str, str, dict[str, Any]]:
    """
    Returns (subject, message_mycode, raw_json_dict).
    """
    prompt = build_user_prompt(topic)
    raw = generate_article(prompt)
    subject = str(raw.get("title") or topic.subject).strip() or topic.subject
    body = article_to_mycode(raw)
    return subject, body, raw
