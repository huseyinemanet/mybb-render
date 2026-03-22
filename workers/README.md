# İçerik motoru (kurallı pipeline)

Bu klasör, plandaki **Faz 2–5** için dış orkestratörün (Python veya Node) yerini tutar. MyBB tarafında hazır olanlar:

- `scripts/migrate_automation_tables.php` — `forum_seed_map`, `content_meta`, `thread_intent_index`, `thread_seed_keys`
- `scripts/seed_game_forums.php` — kategori / forum ağacı
- `scripts/seed_threads.php` — açılış konuları
- `publish_bridge.php` — `MYBB_PUBLISH_SECRET` + başlık `X-MyBB-Publish-Secret` ile JSON POST

## Örnek cron (sunucuda)

```bash
# Günlük: öneri topla, üret, QC, publish_bridge'e POST (kendi worker'ınız)
0 5 * * * cd /var/www/html && python3 workers/pipeline_stub.py >> /tmp/mybb-worker.log 2>&1
```

## Ortam değişkenleri

- `MYBB_PUBLISH_SECRET` — zorunlu (HTTP yayın)
- `MYBB_PUBLISH_UID` — konu sahibi kullanıcı id (varsayılan 1)

## Sonraki adımlar (implementasyon)

1. Keşif: başlık fikirleri topla (tam metin kopyalama yok).
2. Planlama: hedef `fid` / içerik tipi / öncelik.
3. Dedupe: `thread_intent_index` ve `content_meta.source_topic_key`.
4. LLM: yapılandırılmış JSON çıktı → MyCode gövdeye çevir.
5. QC: kurallar veya ikinci model.
6. `publish_bridge.php` veya CLI'da `mybb_publish_new_thread()`.

`pipeline_stub.py` yalnızca iskelet ve çıkış kodudur; ağ ve API anahtarlarını kendiniz bağlarsınız.
