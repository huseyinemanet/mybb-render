#!/usr/bin/env php
<?php
/**
 * Seed forums/categories from data/forums_seed.json (plan-aligned).
 *
 * Options:
 *   --dry-run
 *   --apply
 *   --append-only          Skip slugs already in forum_seed_map
 *   --seed-max-phase=N     Only nodes with seed_phase <= N (hubs use 1 or 2; omit = all)
 *   --reset-seeded         Remove forums tracked in forum_seed_map (forums must be empty unless --force)
 *   --force                With reset: allow non-empty forums (destructive)
 *   --json=path            Alternate JSON file
 */

chdir(dirname(__DIR__));

define('IN_MYBB', 1);
define('NO_ONLINE', 1);
define('NO_PLUGINS', 1);
define('THIS_SCRIPT', 'seed_game_forums.php');

require_once dirname(__DIR__).'/inc/mybb_cli_bootstrap.php';

$dry = in_array('--dry-run', $argv, true);
$apply = in_array('--apply', $argv, true);
$appendOnly = in_array('--append-only', $argv, true);
$reset = in_array('--reset-seeded', $argv, true);
$force = in_array('--force', $argv, true);

$maxPhase = null;
$jsonPath = dirname(__DIR__).'/data/forums_seed.json';

foreach($argv as $arg)
{
	if(strpos($arg, '--seed-max-phase=') === 0)
	{
		$maxPhase = (int)substr($arg, strlen('--seed-max-phase='));
	}
	if(strpos($arg, '--json=') === 0)
	{
		$jsonPath = substr($arg, 7);
		if($jsonPath[0] !== '/')
		{
			$jsonPath = dirname(__DIR__).'/'.$jsonPath;
		}
	}
}

if(!$dry && !$apply)
{
	fwrite(STDERR, "Specify --dry-run or --apply\n");
	exit(1);
}

if($dry && $apply)
{
	fwrite(STDERR, "Use only one of --dry-run or --apply\n");
	exit(1);
}

if(!is_readable($jsonPath))
{
	fwrite(STDERR, "Cannot read JSON: {$jsonPath}\n");
	exit(1);
}

$raw = file_get_contents($jsonPath);
$nodes = json_decode($raw, true);
if(!is_array($nodes))
{
	fwrite(STDERR, "Invalid JSON\n");
	exit(1);
}

global $db, $cache;

function automation_forum_seed_map_exists()
{
	global $db;
	$name = TABLE_PREFIX.'forum_seed_map';
	if($db->type == 'pgsql')
	{
		$r = $db->query("SELECT EXISTS (
			SELECT 1 FROM pg_catalog.pg_class c
			JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
			WHERE n.nspname = 'public' AND c.relname = '".$db->escape_string($name)."')");
		$row = $db->fetch_array($r);
		return !empty($row['exists']);
	}
	$r = $db->query("SHOW TABLES LIKE '".$db->escape_string($name)."'");
	return $db->num_rows($r) > 0;
}

if($apply && !automation_forum_seed_map_exists())
{
	fwrite(STDERR, "Table ".TABLE_PREFIX."forum_seed_map missing. Run: php scripts/migrate_automation_tables.php --apply\n");
	exit(1);
}

/**
 * @return array<string,int>
 */
function load_seed_slug_map()
{
	global $db;
	$out = array();
	$q = $db->simple_select('forum_seed_map', 'slug,fid');
	while($row = $db->fetch_array($q))
	{
		$out[$row['slug']] = (int)$row['fid'];
	}
	return $out;
}

if($reset)
{
	if(!automation_forum_seed_map_exists())
	{
		fwrite(STDERR, "Table ".TABLE_PREFIX."forum_seed_map missing.\n");
		exit(1);
	}
	$slugToFid = load_seed_slug_map();
	if(empty($slugToFid))
	{
		echo "Nothing to reset.\n";
		exit(0);
	}

	$fids = array_values($slugToFid);
	$fidList = implode(',', array_map('intval', $fids));

	$q = $db->simple_select('threads', 'COUNT(*) AS c', "fid IN ({$fidList})");
	$tc = (int)$db->fetch_field($q, 'c');
	if($tc > 0 && !$force)
	{
		fwrite(STDERR, "Refusing reset: {$tc} thread(s) in seeded forums. Use --force to override.\n");
		exit(1);
	}

	if($dry)
	{
		echo "Would delete forums fids: {$fidList}\n";
		exit(0);
	}

	// Depth: more commas in parentlist => deeper child first
	$rows = array();
	$q = $db->simple_select('forums', '*', "fid IN ({$fidList})");
	while($row = $db->fetch_array($q))
	{
		$rows[] = $row;
	}
	usort($rows, function ($a, $b) {
		$da = substr_count($a['parentlist'], ',');
		$db_ = substr_count($b['parentlist'], ',');
		return $db_ <=> $da;
	});

	foreach($rows as $forum)
	{
		$fid = (int)$forum['fid'];
		$db->delete_query('forumpermissions', "fid='{$fid}'");
		$db->delete_query('forums', "fid='{$fid}'");
		echo "Deleted forum fid={$fid} {$forum['name']}\n";
	}

	$db->delete_query('forum_seed_map', '1=1');
	$cache->update_forums();
	$cache->update_forumpermissions();
	echo "Reset complete.\n";
	exit(0);
}

$filtered = array();
foreach($nodes as $n)
{
	$phase = isset($n['seed_phase']) ? (int)$n['seed_phase'] : 0;
	if($maxPhase !== null && $phase > $maxPhase)
	{
		continue;
	}
	$filtered[] = $n;
}
$nodes = $filtered;

$slugToFid = ($apply || $reset || $appendOnly) && automation_forum_seed_map_exists()
	? load_seed_slug_map()
	: array();

if($appendOnly)
{
	$before = count($nodes);
	$nodes = array_values(array_filter($nodes, function ($n) use ($slugToFid) {
		return empty($slugToFid[$n['slug']]);
	}));
	echo "append-only: {$before} -> ".count($nodes)." node(s) to process\n";
}

/**
 * Default permissions: inherit from usergroups for all groups.
 */
function seed_save_inherit_all_perms($fid)
{
	global $db, $cache, $inherit, $canview, $canpostthreads, $canpostreplies, $canpostpolls, $canpostattachments;

	$inherit = array();
	$canview = $canpostthreads = $canpostreplies = $canpostpolls = $canpostattachments = array();

	$q = $db->simple_select('usergroups', 'gid');
	while($g = $db->fetch_array($q))
	{
		$inherit[(int)$g['gid']] = 1;
	}

	save_quick_perms((int)$fid);
}

$bySlug = array();
foreach($nodes as $n)
{
	$bySlug[$n['slug']] = $n;
}

$resolved = array();

foreach($nodes as $n)
{
	$slug = $n['slug'];
	if(isset($slugToFid[$slug]))
	{
		$resolved[$slug] = $slugToFid[$slug];
		continue;
	}

	$pid = 0;
	if(!empty($n['parent_slug']))
	{
		if(empty($resolved[$n['parent_slug']]))
		{
			fwrite(STDERR, "Parent not resolved for {$slug}: {$n['parent_slug']}\n");
			exit(1);
		}
		$pid = $resolved[$n['parent_slug']];
	}

	$type = $n['type'];
	if($type === 'f' && $pid <= 0)
	{
		fwrite(STDERR, "Forum {$slug} needs parent\n");
		exit(1);
	}

	$insert = array(
		'name' => $db->escape_string($n['title']),
		'description' => $db->escape_string($n['description']),
		'linkto' => '',
		'type' => $db->escape_string($type),
		'pid' => (int)$pid,
		'parentlist' => '',
		'disporder' => (int)$n['disporder'],
		'active' => 1,
		'open' => 1,
		'allowhtml' => 0,
		'allowmycode' => 1,
		'allowsmilies' => 1,
		'allowimgcode' => 1,
		'allowvideocode' => 1,
		'allowpicons' => 1,
		'allowtratings' => 1,
		'usepostcounts' => 1,
		'usethreadcounts' => 1,
		'requireprefix' => 0,
		'password' => '',
		'showinjump' => 1,
		'style' => 0,
		'overridestyle' => 0,
		'rulestype' => 0,
		'rulestitle' => '',
		'rules' => '',
		'defaultdatecut' => 0,
		'defaultsortby' => '',
		'defaultsortorder' => '',
	);

	if($dry)
	{
		echo "[dry-run] INSERT {$type} slug={$slug} pid={$pid} title={$n['title']}\n";
		$fake = 90000 + count($resolved);
		$resolved[$slug] = $fake;
		continue;
	}

	$fid = $db->insert_query('forums', $insert);
	$fid = (int)$fid;
	// PostgreSQL driver may return 0 when serial/PK introspection fails; recover from DB.
	if($fid <= 0)
	{
		$mq = $db->simple_select('forums', 'MAX(fid) AS m');
		$fid = (int)$db->fetch_field($mq, 'm');
	}
	if($fid <= 0)
	{
		fwrite(STDERR, "Failed to obtain fid after insert (slug={$slug})\n");
		exit(1);
	}

	$parentlist = make_parent_list($fid);
	$db->update_query('forums', array('parentlist' => $parentlist), "fid='{$fid}'");

	global $pforumcache;
	$pforumcache = false;

	$cache->update_forums();

	seed_save_inherit_all_perms($fid);

	$db->insert_query('forum_seed_map', array(
		'slug' => $db->escape_string($slug),
		'fid' => $fid,
	));

	$resolved[$slug] = $fid;
	$slugToFid[$slug] = $fid;

	echo "Created fid={$fid} slug={$slug} {$n['title']}\n";
}

if($apply && !$dry)
{
	global $pforumcache;
	$pforumcache = false;
	$q = $db->simple_select('forums', 'fid');
	while($row = $db->fetch_array($q))
	{
		$fid = (int)$row['fid'];
		$pl = make_parent_list($fid);
		$db->update_query('forums', array('parentlist' => $pl), "fid='{$fid}'");
		$pforumcache = false;
	}
	$cache->update_forums();
	echo "Rebuilt parentlist for all forums.\n";
}

echo "Done.\n";
