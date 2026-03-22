<?php
/**
 * Read-only forum slug → fid map for automation workers (no DB creds on CI).
 * Auth: header X-MyBB-Publish-Secret must equal MYBB_PUBLISH_SECRET (same as publish_bridge).
 * GET → JSON { "ok": true, "slug_to_fid": { "forum_pop_gta": 28, ... } }
 */

define('IN_MYBB', 1);
define('THIS_SCRIPT', 'forum_map_bridge.php');

require_once __DIR__.'/global.php';

header('Content-Type: application/json; charset=utf-8');

if($_SERVER['REQUEST_METHOD'] !== 'GET')
{
	http_response_code(405);
	echo json_encode(array('error' => 'method_not_allowed'));
	exit;
}

$secret = getenv('MYBB_PUBLISH_SECRET') ?: '';
$hdr = isset($_SERVER['HTTP_X_MYBB_PUBLISH_SECRET']) ? (string)$_SERVER['HTTP_X_MYBB_PUBLISH_SECRET'] : '';
if($secret === '' || $hdr === '' || !hash_equals($secret, $hdr))
{
	http_response_code(401);
	echo json_encode(array('error' => 'unauthorized'));
	exit;
}

require_once MYBB_ROOT.'inc/mybb_publish.php';

global $db;

$map = array();
if(automation_forum_seed_map_exists())
{
	$q = $db->simple_select('forum_seed_map', 'slug,fid');
	while($row = $db->fetch_array($q))
	{
		$map[$row['slug']] = (int)$row['fid'];
	}
}

echo json_encode(array('ok' => true, 'slug_to_fid' => $map));
exit;
