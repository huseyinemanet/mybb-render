# İçerik worker — zamanlama ve sırlar

MyBB web servisi PHP konteynerinde çalışır; **Python worker ayrı tetiklenir** (ör. GitHub Actions).

## GitHub Actions (önerilen, ücretsiz)

1. Repo → **Settings** → **Secrets and variables** → **Actions** → şunları ekle:
   - `MYBB_BASE_URL` — canlı forum kökü (`https://....onrender.com`)
   - `MYBB_PUBLISH_SECRET` — Render’da tanımlı ile aynı
   - `OPENAI_API_KEY` veya `ANTHROPIC_API_KEY`
   - İsteğe bağlı: `DATABASE_URL` (Render PostgreSQL **External** connection string) — ön-dedupe ve doğru `fid` için `forum_seed_map` okunur
   - İsteğe bağlı: `MYBB_TABLE_PREFIX` — `DATABASE_URL` kullanıyorsan forum prefix’inle aynı olmalı
   - İsteğe bağlı: `LLM_PROVIDER` (`anthropic`), `MAX_PUBLISH_PER_RUN` (başlangıçta `1`)

2. Workflow [.github/workflows/content-pipeline.yml](.github/workflows/content-pipeline.yml) günde **3 kez** çalışır (UTC):
   - `03:00`, `10:00`, `17:00` UTC → Türkiye saati (UTC+3) ile yaklaşık **06:00, 13:00, 20:00**.

3. **Manuel deneme:** Actions sekmesinden **Run workflow** (aynı workflow `workflow_dispatch` destekler).

4. **Dakika limiti:** Aşırı LLM çağrısından kaçınmak için `MAX_PUBLISH_PER_RUN=1` bırak; günlerce gözlemledikten sonra `2`–`5` yap.

## Render PostgreSQL dışarıdan

`DATABASE_URL` kullanacaksan Render DB panelinde **Allow connections from outside** (veya eşdeğeri) açık olmalı; aksi halde sadece `MYBB_BASE_URL` + `publish_bridge` yeterli olur (ön-dedupe olmadan).

## `WORKER_FORUM_FIDS_JSON` yedek

Veritabanı okuması yoksa, slug → `fid` eşlemesini elle ver:

```json
{"forum_pop_gta":28,"forum_guides_save":15}
```

Değeri tek satır env olarak ekle (tırnaklara dikkat).

## Saat dilimi notu

GitHub `schedule` her zaman **UTC** kullanır. Kış saati değişirse workflow’daki `cron` satırlarını güncelle.
