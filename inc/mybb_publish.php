<?php
/**
 * Programmatic thread creation for automation / publish_bridge.
 * Caller must have loaded MyBB (e.g. global.php) and set $mybb->user to a permitted account.
 */

if(!defined('IN_MYBB'))
{
	die('Direct access');
}

require_once MYBB_ROOT.'inc/mybb_automation_user.php';

/**
 * @param int    $fid
 * @param string $subject
 * @param string $message  MyBB MyCode-safe body
 * @param int    $uid      Author user id
 * @param array  $meta     Optional: source_topic_key, canonical_intent, game_name, content_type, quality_score
 * @return array{tid:int,pid:int}|array{error:string}
 */
function mybb_publish_new_thread($fid, $subject, $message, $uid, array $meta = array())
{
	global $db, $mybb, $session, $lang;

	$fid = (int)$fid;
	$uid = (int)$uid;

	$forum = get_forum($fid);
	if(!$forum || $forum['type'] != 'f' || $forum['linkto'] != '')
	{
		return array('error' => 'invalid_forum');
	}

	if(!mybb_automation_load_user($uid))
	{
		return array('error' => 'invalid_user');
	}

	if(!empty($meta['canonical_intent']) && automation_thread_intent_exists())
	{
		$key = mybb_normalize_intent($meta['canonical_intent']);
		$q = $db->simple_select('thread_intent_index', 'tid', "normalized_intent='".$db->escape_string($key)."'", array('limit' => 1));
		if($db->num_rows($q) > 0)
		{
			return array('error' => 'duplicate_intent', 'tid' => (int)$db->fetch_field($q, 'tid'));
		}
	}

	if(!empty($meta['source_topic_key']) && automation_content_meta_exists())
	{
		$q = $db->simple_select('content_meta', 'tid', "source_topic_key='".$db->escape_string($meta['source_topic_key'])."'", array('limit' => 1));
		if($db->num_rows($q) > 0)
		{
			return array('error' => 'duplicate_source_key', 'tid' => (int)$db->fetch_field($q, 'tid'));
		}
	}

	require_once MYBB_ROOT.'inc/datahandlers/post.php';
	$lang->load('datahandler_post');

	if(!is_object($session))
	{
		require_once MYBB_ROOT.'inc/class_session.php';
		$session = new session;
		$session->init();
	}

	$posthandler = new PostDataHandler('insert');
	$posthandler->action = 'thread';
	$posthandler->admin_override = true;

	$new_thread = array(
		'fid' => $fid,
		'subject' => $subject,
		'prefix' => 0,
		'icon' => 0,
		'uid' => $mybb->user['uid'],
		'username' => $mybb->user['username'],
		'message' => $message,
		'dateline' => TIME_NOW,
		'ipaddress' => $session->packedip,
		'posthash' => md5($mybb->user['uid'].random_str(4)),
		'savedraft' => 0,
		'options' => array(
			'signature' => 0,
			'subscriptionmethod' => 0,
			'disablesmilies' => 0,
		),
		'modoptions' => array(),
	);

	$posthandler->set_data($new_thread);

	if(!$posthandler->validate_thread())
	{
		return array('error' => 'validation', 'details' => $posthandler->get_friendly_errors());
	}

	$info = $posthandler->insert_thread();
	$tid = (int)$info['tid'];
	$pid = (int)$info['pid'];

	if($tid <= 0)
	{
		return array('error' => 'insert_failed');
	}

	if(automation_content_meta_exists() && !empty($meta['source_topic_key']))
	{
		$db->insert_query('content_meta', array(
			'source_topic_key' => $db->escape_string($meta['source_topic_key']),
			'canonical_intent' => $db->escape_string($meta['canonical_intent'] ?? ''),
			'generated_slug' => $db->escape_string($meta['generated_slug'] ?? ''),
			'tid' => $tid,
			'pid' => $pid,
			'game_name' => $db->escape_string($meta['game_name'] ?? ''),
			'content_type' => $db->escape_string($meta['content_type'] ?? ''),
			'published_at' => TIME_NOW,
			'quality_score' => isset($meta['quality_score']) ? (float)$meta['quality_score'] : 0,
			'update_due_at' => (int)($meta['update_due_at'] ?? 0),
			'source_fingerprint' => $db->escape_string($meta['source_fingerprint'] ?? ''),
		));
	}

	if(automation_thread_intent_exists() && !empty($meta['canonical_intent']))
	{
		$key = mybb_normalize_intent($meta['canonical_intent']);
		$db->insert_query('thread_intent_index', array(
			'normalized_intent' => $db->escape_string($key),
			'tid' => $tid,
		));
	}

	return array('tid' => $tid, 'pid' => $pid);
}

function mybb_normalize_intent($s)
{
	$s = my_strtolower(trim(preg_replace('/\s+/', ' ', (string)$s)));
	return my_substr($s, 0, 250);
}

function automation_content_meta_exists()
{
	global $db;
	return automation_pg_table_exists(TABLE_PREFIX.'content_meta');
}

function automation_thread_intent_exists()
{
	global $db;
	return automation_pg_table_exists(TABLE_PREFIX.'thread_intent_index');
}

function automation_pg_table_exists($name)
{
	global $db;
	if($db->type != 'pgsql')
	{
		$r = $db->query("SHOW TABLES LIKE '".$db->escape_string($name)."'");
		return $db->num_rows($r) > 0;
	}
	$r = $db->query("SELECT EXISTS (
		SELECT 1 FROM pg_catalog.pg_class c
		JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
		WHERE n.nspname = 'public' AND c.relname = '".$db->escape_string($name)."')");
	$row = $db->fetch_array($r);
	return !empty($row['exists']);
}
