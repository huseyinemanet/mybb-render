# İçerik motoru (Python worker)

Zamanlanmış **servis** mantığı: bu kod MyBB Docker imajında çalışmaz (imajda Python yok). **GitHub Actions**, ayrı bir worker sunucusu veya `cron` ile repo kökünden tetiklenir.

## Akış

1. **discovery** — [data/topic_candidates.yaml](data/topic_candidates.yaml) adayları okur.
2. **planner** — `forum_slug`, `subject`, `source_topic_key`, `canonical_intent` üretir (`planner.py`).
3. **dedupe** — İsteğe bağlı PostgreSQL ile `content_meta` / `thread_intent_index` ön filtresi (`dedupe.py`).
4. **generate** — OpenAI veya Anthropic ile JSON makale → MyBB MyCode (`generate.py`, `llm_client.py`).
5. **qc** — Kural tabanlı kalite kapısı (`qc.py`).
6. **publish** — `POST /publish_bridge.php` (`publish.py`).

## Kurulum

```bash
cd /path/to/mybb
python3 -m venv .venv-worker
source .venv-worker/bin/activate   # Windows: .venv-worker\Scripts\activate
pip install -r workers/requirements.txt
```

## Ortam değişkenleri

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `MYBB_BASE_URL` | Evet* | Örn. `https://forum.example.com` |
| `MYBB_PUBLISH_SECRET` | Evet* | `publish_bridge.php` ile aynı |
| `OPENAI_API_KEY` | LLM için | Varsayılan sağlayıcı OpenAI |
| `ANTHROPIC_API_KEY` | Alternatif | `LLM_PROVIDER=anthropic` ile |
| `LLM_PROVIDER` | Hayır | `openai` (varsayılan) veya `anthropic` |
| `MYBB_PUBLISH_UID` | Hayır | Konu yazarı uid (varsayılan 1) |
| `MAX_PUBLISH_PER_RUN` | Hayır | Varsayılan `1` — kademeli artır |
| `MAX_CANDIDATES_PLAN` | Hayır | Planlanan aday üst sınırı (varsayılan 25) |
| `DATABASE_URL` veya `MYBB_DB_*` | Hayır | Ön-dedupe + `forum_seed_map` → `fid` |
| `MYBB_TABLE_PREFIX` | DB ile | Örn. `sh2ufntmhy_` |
| `WORKER_FORUM_FIDS_JSON` | Hayır | `{"forum_pop_gta": 28}` yedek fid haritası |
| `DRY_RUN` | Hayır | `1` = yayınlamaz, sadece log |
| `SKIP_LLM` | Hayır | `1` = sahte gövde (smoke test) |
| `TOPIC_CANDIDATES_PATH` | Hayır | Özel YAML yolu |

\* `DRY_RUN=1` iken `MYBB_PUBLISH_SECRET` gerekmez.

## Yerel çalıştırma

```bash
export MYBB_BASE_URL="https://..."
export MYBB_PUBLISH_SECRET="..."
export OPENAI_API_KEY="..."
export DATABASE_URL="postgresql://..."   # önerilir: fid + ön dedupe
export MYBB_TABLE_PREFIX="sh2ufntmhy_"
python -m workers.pipeline
```

Smoke test (API yok):

```bash
DRY_RUN=1 SKIP_LLM=1 python -m workers.pipeline
```

## `source_topic_key` ve `canonical_intent`

- **`source_topic_key`**: ASCII slug; `content_meta` satırı ile bire bir eşleşir. Biçim: `auto-{template_key}-{game}` (bkz. `planner._slugify_key`).
- **`canonical_intent`**: MyBB `thread_intent_index` için normalize edilmiş niyet metni; aynı konuyu farklı başlıklarla tekrar açmayı azaltır. Şablon başına sabit kalıplar `planner._template_subject_and_intent` içindedir.

## GitHub Actions

Bkz. [.github/workflows/content-pipeline.yml](../.github/workflows/content-pipeline.yml) ve [DEPLOY_WORKER.md](../DEPLOY_WORKER.md).
