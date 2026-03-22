#!/usr/bin/env php
<?php
/**
 * Creates automation helper tables (forum seed map, content meta, thread intent index).
 *
 * Usage: php scripts/migrate_automation_tables.php --dry-run | --apply
 */

chdir(dirname(__DIR__));

define('IN_MYBB', 1);
define('NO_ONLINE', 1);
define('NO_PLUGINS', 1);
define('THIS_SCRIPT', 'migrate_automation_tables.php');

require_once dirname(__DIR__).'/inc/mybb_cli_bootstrap.php';

$dry = in_array('--dry-run', $argv, true);
$apply = in_array('--apply', $argv, true);

if(!$dry && !$apply)
{
	fwrite(STDERR, "Specify --dry-run or --apply\n");
	exit(1);
}

$prefix = TABLE_PREFIX;
$tables = array();

$tables[] = "CREATE TABLE IF NOT EXISTS {$prefix}forum_seed_map (
	slug varchar(64) NOT NULL,
	fid int NOT NULL,
	PRIMARY KEY (slug)
);";

$tables[] = "CREATE TABLE IF NOT EXISTS {$prefix}content_meta (
	id serial NOT NULL,
	source_topic_key varchar(190) NOT NULL,
	canonical_intent text,
	generated_slug varchar(190),
	tid int NOT NULL default 0,
	pid int NOT NULL default 0,
	game_name varchar(120),
	content_type varchar(40),
	published_at int NOT NULL default 0,
	quality_score double precision,
	update_due_at int NOT NULL default 0,
	source_fingerprint varchar(64),
	PRIMARY KEY (id),
	UNIQUE (source_topic_key)
);";

$tables[] = "CREATE TABLE IF NOT EXISTS {$prefix}thread_intent_index (
	normalized_intent varchar(255) NOT NULL,
	tid int NOT NULL,
	PRIMARY KEY (normalized_intent)
);";

$tables[] = "CREATE TABLE IF NOT EXISTS {$prefix}thread_seed_keys (
	source_key varchar(190) NOT NULL,
	tid int NOT NULL,
	PRIMARY KEY (source_key)
);";

foreach($tables as $sql)
{
	if($dry)
	{
		echo $sql."\n\n";
	}
	else
	{
		$db->write_query($sql);
		echo "OK\n";
	}
}

if($apply)
{
	echo "Migration applied.\n";
}
