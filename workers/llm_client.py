"""OpenAI or Anthropic JSON generation (structured article)."""

from __future__ import annotations

import json
import os
import re
from typing import Any


ARTICLE_JSON_INNER: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "intro": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "heading": {"type": "string"},
                    "paragraphs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["heading", "paragraphs", "bullets"],
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
        "internal_link_hints": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "intro", "sections", "warnings", "internal_link_hints"],
}

OPENAI_JSON_SCHEMA_WRAPPER: dict[str, Any] = {
    "name": "forum_article",
    "strict": True,
    "schema": ARTICLE_JSON_INNER,
}


def _system_rules() -> str:
    return """Sen Türkçe yazan bir oyun rehberi editörüsün.
Kurallar:
- Sadece tek oyunculu / offline içerik; çok oyunculu hile, exploit, ban riski yok.
- Kesin yalan veya korsan teşvik etme; sürüm farklarını belirt.
- Çıktı SADECE istenen JSON şemasına uysun; markdown code fence kullanma.
- İçerik özet ve şablon niteliğinde olsun; kısa ama yapılandırılmış bölümler kullan.
"""


def generate_article_openai(
    user_prompt: str,
    model: str | None = None,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    m = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=m,
        messages=[
            {"role": "system", "content": _system_rules()},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": OPENAI_JSON_SCHEMA_WRAPPER,
        },
    )
    text = resp.choices[0].message.content or "{}"
    return json.loads(text)


def generate_article_anthropic(user_prompt: str, model: str | None = None) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    m = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    schema_str = json.dumps(ARTICLE_JSON_INNER)
    msg = client.messages.create(
        model=m,
        max_tokens=4096,
        system=_system_rules()
        + "\nYanıtın tek bir JSON nesnesi olmalı ve şu şemaya uymalı:\n"
        + schema_str,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = ""
    for block in msg.content:
        if hasattr(block, "text"):
            text += block.text
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def resolve_llm_provider() -> str:
    """Explicit LLM_PROVIDER wins; else Anthropic-only key selects anthropic."""
    p = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if p in ("anthropic", "openai"):
        return p
    ak = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    ok = os.environ.get("OPENAI_API_KEY", "").strip()
    if ak and not ok:
        return "anthropic"
    return "openai"


def generate_article(user_prompt: str) -> dict[str, Any]:
    if resolve_llm_provider() == "anthropic":
        return generate_article_anthropic(user_prompt)
    return generate_article_openai(user_prompt)
