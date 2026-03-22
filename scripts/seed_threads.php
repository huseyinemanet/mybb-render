#!/usr/bin/env php
<?php
/**
 * Seed initial threads (weighted toward high-traffic forums). Idempotent via thread_seed_keys.
 *
 * Prerequisites: migrate_automation_tables.php --apply, seed_game_forums.php --apply
 *
 * Options: --dry-run | --apply | --append-only
 */

chdir(dirname(__DIR__));

define('IN_MYBB', 1);
define('NO_ONLINE', 1);
define('NO_PLUGINS', 1);
define('THIS_SCRIPT', 'seed_threads.php');

require_once dirname(__DIR__).'/inc/mybb_cli_bootstrap.php';

require_once MYBB_ROOT.'inc/class_session.php';
$session = new session;
$session->init();

require_once MYBB_ROOT.'inc/mybb_publish.php';

$dry = in_array('--dry-run', $argv, true);
$apply = in_array('--apply', $argv, true);
$appendOnly = in_array('--append-only', $argv, true);

if(!$dry && !$apply)
{
	fwrite(STDERR, "Specify --dry-run or --apply\n");
	exit(1);
}

global $db;

function seed_thread_keys_table_ok()
{
	global $db;
	if($db->type != 'pgsql')
	{
		$r = $db->query("SHOW TABLES LIKE '".TABLE_PREFIX."thread_seed_keys'");
		return $db->num_rows($r) > 0;
	}
	$r = $db->query("SELECT EXISTS (
		SELECT 1 FROM pg_catalog.pg_class c
		JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
		WHERE n.nspname = 'public' AND c.relname = '".TABLE_PREFIX."thread_seed_keys')");
	$row = $db->fetch_array($r);
	return !empty($row['exists']);
}

if($apply && !seed_thread_keys_table_ok())
{
	fwrite(STDERR, "Run: php scripts/migrate_automation_tables.php --apply\n");
	exit(1);
}

function load_forum_slug_map()
{
	global $db;
	$map = array();
	$q = $db->simple_select('forum_seed_map', 'slug,fid');
	while($row = $db->fetch_array($q))
	{
		$map[$row['slug']] = (int)$row['fid'];
	}
	return $map;
}

function load_existing_thread_keys()
{
	global $db;
	$k = array();
	if(!seed_thread_keys_table_ok())
	{
		return $k;
	}
	$q = $db->simple_select('thread_seed_keys', 'source_key');
	while($row = $db->fetch_array($q))
	{
		$k[$row['source_key']] = true;
	}
	return $k;
}

function build_seed_topics()
{
	$y = (int)gmdate('Y');

	$topics = array();

	$add = function ($forum_slug, $source_key, $subject, $msg) use (&$topics) {
		$topics[] = array(
			'forum_slug' => $forum_slug,
			'source_key' => $source_key,
			'subject' => $subject,
			'message' => $msg,
		);
	};

	$simple = function ($game, $forum_slug, $suffix, $lines, $key_suffix = '') use ($add, $y) {
		$base = preg_replace('/[^a-zA-Z0-9]+/', '-', my_strtolower($game));
		$sk = trim($base.'-'.preg_replace('/\s+/', '-', my_strtolower($suffix)).($key_suffix !== '' ? '-'.$key_suffix : ''), '-');
		$subj = $game.' '.$suffix.($suffix === 'hileleri tam liste' ? " ({$y})" : '');
		$msg = "[b]Özet[/b]\n{$game} için {$suffix}.\n\n[b]Platform[/b]\nSürümünüzü belirtin.\n\n[b]Detay[/b]\n".implode("\n", $lines)."\n\n[i]Resmi kaynak ve yama notlarını kontrol edin.[/i]";
		$add($forum_slug, $sk, $subj, $msg);
	};

	$gta = array('GTA III', 'GTA Vice City', 'GTA San Andreas', 'GTA IV', 'GTA V');
	foreach($gta as $g)
	{
		$simple($g, 'forum_pop_gta', 'hileleri tam liste', array('Tek oyunculu kodları kullanın.', 'Online modda hile kullanmayın.'));
		$simple($g, 'forum_pop_gta', 'görev rehberi giriş', array('Ana görev sırası ve yan içerikler için ayrı konular açılabilir.'));
	}
	$add('forum_pop_gta', 'gta-save-locations', 'GTA serisi save dosyası nerede (PC)', "[b]Save / config[/b]\nOyun sürümüne göre Belgeler veya kullanıcı klasörü altında konum değişir.\n\n[b]Yedek[/b]\nDeğişiklik öncesi kopya alın.");

	$skyrim = array('Skyrim SE', 'Skyrim AE', 'Oblivion');
	foreach($skyrim as $g)
	{
		$simple($g, 'forum_pop_tes', 'enchanting rehberi giriş', array('Beceri, eşya ve yüzük kombinasyonları için detaylı rehber açılabilir.'));
		$simple($g, 'forum_pop_tes', 'görev takılı kaldım çözümü', array('Quest ID ve aşama notları eklenebilir.'));
	}
	$add('forum_pop_tes', 'skyrim-save-path', 'Skyrim save dosyası konumu Steam', "[b]Save[/b]\nSteam kullanıcı verisi altında saklanır.\n\n[b]Yedek[/b]\nOyun kapalıyken kopyalayın.");

	$cp = array('Cyberpunk 2077');
	foreach($cp as $g)
	{
		$simple($g, 'forum_pop_cyberpunk', 'fps artırma ayarları', array('DLSS/FSR, gölgeler, trafik yoğunluğu.', 'Sürücü ve Windows oyun modu.'));
		$simple($g, 'forum_pop_cyberpunk', 'build önerisi başlangıç', array('Netrunner, Solo, Tech — oynanış tarzına göre.'));
		$simple($g, 'forum_guides_save', 'save dosyası yedekleme', array('Manuel kayıt yolları ve bulut senkron.'));
	}

	$re = array('Resident Evil 4', 'Resident Evil 2 Remake', 'Resident Evil Village');
	foreach($re as $g)
	{
		$simple($g, 'forum_pop_re', 'kasa şifresi çözümü', array('Bölüm bazlı şifreler ayrı konularda toplanabilir.'));
		$simple($g, 'forum_guides_puzzles', 'bulmaca çözümü giriş', array('Eşya kombinasyonları ve sıra.'));
	}

	$pes = array('PES 2013', 'FC 24', 'FIFA 23');
	foreach($pes as $g)
	{
		$simple($g, 'forum_pop_pes_fifa', 'kariyer modu genç oyuncular', array('Potansiyel ve kiralık önerileri genişletilebilir.'));
	}

	$mb = array('Mount & Blade II Bannerlord', 'Warband');
	foreach($mb as $g)
	{
		$simple($g, 'forum_pop_mb', 'başlangıç rehberi', array('Klan, ekonomi ve ordu oluşturma.'));
	}

	for($i = 1; $i <= 8; $i++)
	{
		$add('forum_cheats_pc', 'pc-cheats-generic-'.$i, 'PC konsol komutları kullanımı (oyun '.$i.')', "[b]Konsol[/b]\nOyun içi konsolu destekleyen yapımlarda geçerlidir.\n\n[b]Uyarı[/b]\nBaşarım kilidi riskine dikkat.");
	}

	$add('forum_tech_crash', 'tech-crash-generic', 'Oyun açılmıyor siyah ekran genel kontrol listesi', "[b]Kontrol[/b]\n1) GPU sürücüsü\n2) DX/Vulkan seçimi\n3) Tam ekran pencereli\n4) Yönetici olarak çalıştırma\n5) Dosya doğrulama (Steam)");
	$add('forum_tech_crash', 'tech-crash-vc', 'GTA Vice City Windows 10/11 açılmıyor', "[b]Uyumluluk[/b]\nEski oyunlarda mod ve uyumluluk modu sık gereklidir.\n\n[b]Not[/b]\nYasal kopya ve yama sürümünü belirtin.");
	$add('forum_tech_fps', 'tech-fps-cyberpunk', 'Cyberpunk 2077 düşük FPS optimizasyon', "[b]Ayarlar[/b]\nGölgeler, crowd, efektler.\n[b]Donanım[/b]\nVRAM ve termal sınır.");
	$add('forum_tech_patch', 'patch-tr-template', 'Türkçe yama nasıl kurulur (genel şablon)', "[b]Şablon[/b]\nBelirli oyun için ayrı konu açın: Oyun adı + Türkçe yama nasıl kurulur.\n[b]Kaynak[/b]\nGüvenilir çeviri grubu bağlantıları.");
	$add('forum_tech_patch', 'patch-tr-fail', 'Türkçe yama çalışmıyor çözümü (genel)', "[b]Kontrol[/b]\nSürüm uyumu, antivirüs, dosya yolu (Türkçe karakter).");
	$add('forum_tech_gamepad', 'pad-steam-input', 'Steam Input ile gamepad tanınmıyor', "[b]Çözüm[/b]\nŞablon, deadzone ve Xbox/DS4 seçimi.");

	$add('forum_guides_quests', 'quests-generic', 'Görev rehberi nasıl yazılır (şablon)', "[b]Başlık[/b]\nOyun + görev adı + nasıl yapılır.\n[b]Gövde[/b]\nÖnkoşul, adımlar, ödül, sık hata.");
	$add('forum_lists_lowspec', 'list-lowspec-1', 'Düşük sistem için açık dünya önerileri', "[b]Liste[/b]\nEski donanımda çalışan tek oyunculu yapımlar.");
	$add('forum_lists_story', 'list-story-1', 'Hikâyeli oyun önerileri (giriş listesi)', "[b]Liste[/b]\nLinear hikâye ve güçlü karakter odaklı yapımlar.");
	$add('forum_lists_horror', 'list-horror-1', 'Korku oyun önerileri giriş', "[b]Liste[/b]\nAtmosfer ve survival alt türleri.");
	$add('forum_lists_order', 'list-order-tes', 'The Elder Scrolls oynama sırası önerisi', "[b]Sıra[/b]\nArena → Daggerfall → Morrowind → Oblivion → Skyrim (isteğe bağlı).");

	$add('forum_rules_announce', 'rules-welcome', 'Foruma hoş geldiniz — kurallar özeti', "[b]Tek oyunculu odak[/b]\nÇok oyunculu exploit ve hile paylaşımı yasaktır.\n[b]Kaynak[/b]\nMümkünse resmi veya güvenilir rehber belirtin.");

	$fillers = array(
		array('forum_cheats_ps', 'PlayStation', 'kod listesi giriş'),
		array('forum_cheats_xbox', 'Xbox', 'kod listesi giriş'),
		array('forum_cheats_classic', 'PS2 klasik', 'kodlar ve notlar'),
		array('forum_guides_mods', 'Mod', 'kurulum öncesi yedek'),
		array('forum_guides_100', 'Başarım', 'koleksiyon ipuçları'),
		array('forum_lists_coop', 'Co-op', 'yerel ve online ayrımı'),
	);

	for($n = 0; $n < 35; $n++)
	{
		$f = $fillers[$n % count($fillers)];
		$simple($f[1].' #'.($n + 1), $f[0], $f[2], array('Bu konu trafik ağırlıklı alanlara destek için çoğaltılmış şablondur.'), (string)$n);
	}

	$tech_forums = array('forum_tech_crash', 'forum_tech_fps', 'forum_tech_patch', 'forum_tech_gamepad');
	for($n = 0; $n < 16; $n++)
	{
		$slug = $tech_forums[$n % count($tech_forums)];
		$add($slug, 'tech-bulk-'.$n, 'Teknik sorun şablonu #'.($n + 1).' (genel)', "[b]Başlık standardı[/b]\nOyun adı + sorun + platform.\n[b]Gövde[/b]\nSürüm, hata metni, denenen çözümler.");
	}

	return $topics;
}

$topics = build_seed_topics();

if($appendOnly)
{
	$have = load_existing_thread_keys();
	$before = count($topics);
	$topics = array_values(array_filter($topics, function ($t) use ($have) {
		return empty($have[$t['source_key']]);
	}));
	echo "append-only: {$before} -> ".count($topics)." topic(s)\n";
}

$fmap = load_forum_slug_map();
$uid = (int)(getenv('MYBB_PUBLISH_UID') ?: 1);

foreach($topics as $t)
{
	if(empty($fmap[$t['forum_slug']]))
	{
		fwrite(STDERR, "Missing forum slug in seed map: {$t['forum_slug']}\n");
		exit(1);
	}
	$fid = $fmap[$t['forum_slug']];

	if($dry)
	{
		echo "[dry-run] fid={$fid} {$t['subject']}\n";
		continue;
	}

	$res = mybb_publish_new_thread($fid, $t['subject'], $t['message'], $uid, array(
		'source_topic_key' => $t['source_key'],
		'canonical_intent' => $t['subject'],
		'content_type' => 'seed',
		'quality_score' => 0.5,
	));

	if(!empty($res['error']))
	{
		if($res['error'] === 'duplicate_source_key' || $res['error'] === 'duplicate_intent')
		{
			echo "Skip duplicate {$t['source_key']}\n";
			continue;
		}
		fwrite(STDERR, "Fail {$t['source_key']}: ".json_encode($res)."\n");
		exit(1);
	}

	if(!empty($res['tid']))
	{
		$exists = $db->simple_select('thread_seed_keys', 'source_key', "source_key='".$db->escape_string($t['source_key'])."'", array('limit' => 1));
		if($db->num_rows($exists) == 0)
		{
			$db->insert_query('thread_seed_keys', array(
				'source_key' => $db->escape_string($t['source_key']),
				'tid' => (int)$res['tid'],
			));
		}
		echo "OK tid={$res['tid']} {$t['subject']}\n";
	}
}

echo "Done. Topics processed: ".count($topics)."\n";
