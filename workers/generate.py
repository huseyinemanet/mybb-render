"""Build LLM prompt from PlannedTopic; parse JSON; render MyBB MyCode."""

from __future__ import annotations

from typing import Any

from workers.llm_client import generate_article
from workers.planner import PlannedTopic


def _factual_constraints(topic: PlannedTopic) -> str:
    if topic.content_type == "cheats":
        return """
ZORUNLU — HİLE / KOD ŞABLONU (otomatik yayın güvenliği):
- Tek tek hile kodu, tuş kombinasyonu, konsol komutu veya "KOD: açıklama" satırı YAZMA. Model hafızası kodlarda sık hata yapar.
- Bunun yerine: kodların yalnızca tek oyunculu modda anlamı; platform ve sürüm (orijinal/yeniden yayın) farkları;
  kayıt dosyası / başarı etkisi uyarıları; kodları güvenilir bir wiki veya kılavuzda nasıl aratacakları.
- Bölüm başlıkları genel kalabilir (ör. silah, araç, polis seviyesi) ama içerik somut kod içermesin.
- Karakter veya yer adı kullanacaksan yalnızca kesin bildiğin doğru isimleri yaz; şüphede "ana karakter" gibi genel anlat.
- Uyarılar bölümünde mutlaka güvenilir kaynakta doğrulama ve yedek kaydı tavsiyesi olsun.
"""
    if topic.content_type in ("guide", "tech"):
        return """
ZORUNLU — REHBER / TEKNİK:
- Tam dosya yolu, kayıt klasörü adı, menü öğesi adı veya kesin sürüm numarası uydurma.
- "Genellikle", "çoğu kurulumda", "Windows'ta sık görülen" gibi çerçeve kullan; okuyucuya kendi sürümünde doğrulamasını söyle.
"""
    if topic.content_type == "list":
        return """
ZORUNLU — LİSTE:
- Oyun adı ve tür iddialarını abartma; emin olmadığın yapımı ekleme. Liste maddeleri kısa ve tarafsız olsun.
"""
    return """
Genel: Ölçülebilir teknik iddia (yol, kod, istatistik) uydurma; emin değilsen çerçeve + doğrulama öner.
"""


def build_user_prompt(topic: PlannedTopic) -> str:
    core = f"""Aşağıdaki konu için forum gönderisi üret.

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
    return core + _factual_constraints(topic)


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
