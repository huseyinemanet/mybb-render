"""Build LLM prompt from PlannedTopic; parse JSON; render MyBB MyCode."""

from __future__ import annotations

from typing import Any

from workers.llm_client import generate_article
from workers.planner import PlannedTopic


def _variation_angle(topic: PlannedTopic) -> str:
    angles = [
        "platform ve sürüm farkları",
        "ilk kez deneyenler için hızlı başlangıç",
        "sık yapılan hatalar ve çözüm yolu",
        "zaman kazandıran kısa kontrol listesi",
    ]
    idx = sum(ord(ch) for ch in topic.source_topic_key) % len(angles)
    return angles[idx]


def _type_rubric(topic: PlannedTopic) -> str:
    ct = topic.content_type
    if ct == "cheats":
        return """
İÇERİK TİPİ: cheats
- Amaç arama niyetiyle tam uyum: okuyucu bu başlıkta kod bekliyorsa sınırlı ama işe yarar kod listesi ver.
- cheat_entries alanını doldur: yalnızca yaygın ve canonical olduğu yüksek güvenle bilinen kodlar.
- Sadece confidence=\"high\" kullan; emin olmadığın kodu cheat_entries'e ekleme.
- code alanı kısa ve net olsun; effect bir cümleyi geçmesin; platform_note kısa ve pratik olsun.
- Toplam 5-12 kod hedefle; aynı etkiyi tekrarlayan kodlardan kaçın.
- sections içinde en az 3 bölüm yaz: kullanım notları, platform/sürüm farkları, güvenli kullanım ve doğrulama.
- warnings içinde tek oyunculu sınırı ve kayıt yedeği mutlaka yer alsın.
"""
    if ct == "guide":
        return """
İÇERİK TİPİ: guide
- En az 4 bölüm yaz ve en az 1 bölümün kind değeri howto olsun.
- steps alanını en az bir howto bölümünde 3-7 adım ile doldur.
- Her bölümde somut ilerleme akışı ver; sadece genel tavsiye listesi üretme.
- Oyun içi adlar konusunda emin değilsen genel ama uygulanabilir ifade kullan.
- cheat_entries her zaman [] olmalı.
"""
    if ct == "tech":
        return """
İÇERİK TİPİ: tech
- En az 4 bölüm yaz; sorun tespiti, ayar önerisi, doğrulama ve geri alma mantığına yer ver.
- En az bir howto bölümü üret ve 3-8 adımlık steps kullan.
- Kesin dosya yolu veya sürüm uydurma; bunun yerine platforma göre doğrulama adımı ver.
- Paragraph'larda ölçülebilir beklenti yaz (ör. takılma azalması, stabilite artışı gibi).
- cheat_entries her zaman [] olmalı.
"""
    if ct == "list":
        return """
İÇERİK TİPİ: list
- En az 3 bölüm yaz; seçme kriteri, liste, kime uygun/kime değil ayrımı olsun.
- Liste maddeleri kısa, karşılaştırılabilir ve tekrar etmeyen içerikte olsun.
- Abartılı iddia veya emin olmadığın oyun adı kullanma.
- cheat_entries her zaman [] olmalı.
"""
    return """
İÇERİK TİPİ: article
- En az 3 bölüm yaz; bir bölümde pratik uygulama adımı (steps) ver.
- Yüzeysel kalıp cümlelerden kaçın, okuyucunun işine yarayacak net çıktı üret.
- cheat_entries her zaman [] olmalı.
"""


def build_user_prompt(topic: PlannedTopic) -> str:
    core = f"""Aşağıdaki konu için forum gönderisi üret. İçerik hem güvenli hem gerçekten faydalı olmalı.

Oyun: {topic.game}
İçerik tipi: {topic.content_type}
Şablon: {topic.template_key}
Hedef konu başlığı (thread subject): {topic.subject}
Niyet özeti (canonical): {topic.canonical_intent}
Bu içerikte öne çıkarılacak açı: {_variation_angle(topic)}

JSON alanları:
- title: subject ile uyumlu, net ve clickbait olmayan başlık; tercihen 45-90 karakter
- intro: 2-4 cümle; bu başlığın okuyucuya sağlayacağı değeri doğrudan söyle
- sections: tipe uygun derinlikte bölümler; her bölümde heading, kind, paragraphs, bullets, steps alanları bulunsun
- warnings: 1-3 uyarı (tek oyunculu, sürüm farkı, yedek al vb.)
- internal_link_hints: forumda açılabilecek ilgili konu başlığı önerileri (sadece metin, 2-3 öğe)
- cheat_entries: cheats tipinde 5-12 kayıt, diğer tüm tiplerde []

Metinde şunları yapma: çok oyunculu hile, cheat engine ile online, korsan bağlantı, politika ihlali.
Kullanıcı niyetinden sapma; farklı oyuna veya alakasız konuya kayma.
"""
    return core + _type_rubric(topic)


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
        steps = sec.get("steps") or []
        if steps:
            lines.append("[list=1]")
            for step in steps:
                step = str(step).strip()
                if step:
                    lines.append(f"[*]{step}")
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
        lines.append("")

    cheats = data.get("cheat_entries") or []
    if cheats:
        lines.append("[b]Kod listesi (tek oyunculu)[/b]")
        lines.append("[list]")
        for row in cheats:
            if not isinstance(row, dict):
                continue
            code = str(row.get("code", "")).strip()
            effect = str(row.get("effect", "")).strip()
            note = str(row.get("platform_note", "")).strip()
            if not code or not effect:
                continue
            text = f"[*][b]{code}[/b] - {effect}"
            if note:
                text += f" ({note})"
            lines.append(text)
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
