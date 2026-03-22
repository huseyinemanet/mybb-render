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

## Zamanlanmış içerik worker (Python)

MyBB imajında Python yok; otomatik konu üretimi **GitHub Actions** veya ayrı worker ile çalışır. Kurulum: [DEPLOY_WORKER.md](DEPLOY_WORKER.md).

## Shell Pro yok — otomasyonu nasıl çalıştırırsın?

Render’da **Shell** özelliği ücretli planda. Ücretsiz planda iki yol var.

### A) Deploy sırasında otomatik (önerilen)

1. Render’da **web service** → **Environment** → **Add Environment Variable**
2. Ad: `MYBB_RUN_CLI_AUTOMATION`, değer: `1`
3. **Save**; servis yeniden deploy olur. Container ayağa kalkarken sırayla çalışır:
   - `migrate_automation_tables.php --apply`
   - `seed_game_forums.php --apply --append-only`
   - `seed_threads.php --apply --append-only`
4. Deploy **başarılı** olduktan sonra bu değişkeni **sil** veya `0` yapıp tekrar kaydet. Böylece her uyandırmada seed tekrarlanmaz (zarar vermez ama gereksiz süre yer).

`--append-only` zaten ikinci kez çalışsa da çoğu işi atlar; yine de bayrağı kapatman iyi pratik.

### B) Kendi bilgisayarından (Shell’siz)

1. Render’da **PostgreSQL** → **Connections** / **External Database URL** (veya host, port, user, password, database adı).
2. Mac’te proje klasöründe aynı değerlerle ortam değişkenlerini verip script’leri çalıştır:

```bash
cd /path/to/mybb
export MYBB_DB_TYPE=pgsql
export MYBB_DB_HOST="…"    # Render’ın verdiği host
export MYBB_DB_PORT="5432"
export MYBB_DB_NAME=mybb
export MYBB_DB_USER="…"
export MYBB_DB_PASSWORD="…"
export MYBB_TABLE_PREFIX="sh2ufntmhy_"   # kendi prefix’in neyse
php scripts/migrate_automation_tables.php --apply
php scripts/seed_game_forums.php --apply --append-only
php scripts/seed_threads.php --apply --append-only
```

Prefix’i `inc/config.php` veya Render env’deki `MYBB_TABLE_PREFIX` ile aynı tut.

## Otomasyon script’leri (Docker / Render Shell — Pro)

Shell erişimin varsa, çalışma dizini `/var/www/html`:

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
