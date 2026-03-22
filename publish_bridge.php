<?php
/**
 * HTTP bridge for programmatic thread creation (automation workers).
 *
 * Auth: header X-MyBB-Publish-Secret must equal env MYBB_PUBLISH_SECRET.
 * POST JSON body:
 *   fid (int), subject (string), message (string),
 *   optional: uid (int, default MYBB_PUBLISH_UID or 1),
 *   optional: source_topic_key, canonical_intent, game_name, content_type, quality_score
 */

define('IN_MYBB', 1);
define('THIS_SCRIPT', 'publish_bridge.php');

require_once __DIR__.'/global.php';

header('Content-Type: application/json; charset=utf-8');

if($_SERVER['REQUEST_METHOD'] !== 'POST')
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

$raw = file_get_contents('php://input');
$in = json_decode($raw, true);
if(!is_array($in))
{
	http_response_code(400);
	echo json_encode(array('error' => 'invalid_json'));
	exit;
}

$fid = isset($in['fid']) ? (int)$in['fid'] : 0;
$subject = isset($in['subject']) ? trim((string)$in['subject']) : '';
$message = isset($in['message']) ? (string)$in['message'] : '';
$uid = isset($in['uid']) ? (int)$in['uid'] : (int)(getenv('MYBB_PUBLISH_UID') ?: 1);

if($fid <= 0 || $subject === '' || $message === '')
{
	http_response_code(400);
	echo json_encode(array('error' => 'missing_fields'));
	exit;
}

$meta = array();
foreach(array('source_topic_key', 'canonical_intent', 'game_name', 'content_type', 'generated_slug', 'source_fingerprint') as $k)
{
	if(!empty($in[$k]))
	{
		$meta[$k] = $in[$k];
	}
}
if(isset($in['quality_score']))
{
	$meta['quality_score'] = $in['quality_score'];
}
if(isset($in['update_due_at']))
{
	$meta['update_due_at'] = (int)$in['update_due_at'];
}

require_once MYBB_ROOT.'inc/mybb_publish.php';

$result = mybb_publish_new_thread($fid, $subject, $message, $uid, $meta);

if(isset($result['error']))
{
	$code = 400;
	if($result['error'] === 'duplicate_intent' || $result['error'] === 'duplicate_source_key')
	{
		$code = 409;
	}
	http_response_code($code);
	echo json_encode($result);
	exit;
}

echo json_encode(array('ok' => true, 'tid' => $result['tid'], 'pid' => $result['pid']));
exit;
