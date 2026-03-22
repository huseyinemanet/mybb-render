# MyBB on Render Free

Bu repo Render Free icin Docker ile hazirlandi.

## Bilmen gerekenler

- Render Free web service 15 dakika bos kalinca uyur.
- Render Free PostgreSQL 30 gun sonra expire olur.
- Render Free web service kalici disk vermez; `uploads/` ve benzeri kullanici dosyalari kalici degildir.
- Bu kurulum deneme ve kucuk test ortami icin uygundur, gercek forum icin uygun degildir.

## Gerekli seyler

1. Bir GitHub reposu
2. Bir Render hesabi
3. Bu proje dosyalarinin GitHub'a push edilmis hali

## Render uzerinde kurulum

1. Bu klasoru bir Git reposuna cevir.
2. GitHub'a push et.
3. Render dashboard'da `New +` -> `Blueprint` sec.
4. GitHub reposunu bagla.
5. `render.yaml` dosyasini Render algilayacak.
6. Web service ve PostgreSQL database otomatik olusacak.
7. Web service olustuktan sonra `MYBB_BASE_URL` ve `MYBB_SITE_URL` degiskenlerini Render'in verdigi `https://...onrender.com` adresiyle guncelle.
8. Deploy bitince foruma giris yap ve Admin CP'den ayarlari tekrar kaydet.

## Güvenlik (ACP ve yayın)

- **Basic Auth ve Secret PIN** herhangi bir yerde ifşa olduysa Render Dashboard üzerinden **hemen yenileyin**: `MYBB_ADMIN_BASIC_AUTH_USER`, `MYBB_ADMIN_BASIC_AUTH_PASS`, `MYBB_SECRET_PIN`.
- Otomatik konu yayını için **`MYBB_PUBLISH_SECRET`** tanımlayın (güçlü rastgele dize). Bu değer `publish_bridge.php` isteklerinde zorunludur.
- Üretimde ACP şifrelerini sohbet veya repoya yazmayın.

## Otomasyon script’leri (Docker / Render Shell)

Örnek (çalışma dizini repo kökü, `/var/www/html`):

```bash
php scripts/migrate_automation_tables.php --apply
php scripts/seed_game_forums.php --dry-run
php scripts/seed_game_forums.php --apply --append-only --seed-max-phase=1
php scripts/seed_threads.php --dry-run
php scripts/seed_threads.php --apply --append-only
```

## Notlar

- `inc/config.php` artik DB ayarlarini environment variable'lardan okuyabiliyor.
- `inc/settings.php` artik temel URL ve e-posta degerlerini environment variable'lardan okuyabiliyor.
- Yerel kurulum bilgileri fallback olarak dosyada duruyor; Render ortaminda env degerleri bunlarin ustune gecer.
- Varsayılan dil için `MYBB_BB_LANGUAGE` ve `MYBB_CP_LANGUAGE` ortam değişkenlerini `turkish` yapabilirsiniz (`render.yaml` örnek değerler).
