<?php
/**
 * Load a registered user into $mybb for trusted automation (CLI or publish bridge).
 * Requires inc/init.php already loaded.
 */

if(!defined('IN_MYBB'))
{
	die('Direct access');
}

/**
 * @param int $uid
 * @return bool
 */
function mybb_automation_load_user($uid)
{
	global $db, $mybb;

	$uid = (int)$uid;
	$query = $db->query("
		SELECT u.*, f.*
		FROM ".TABLE_PREFIX."users u
		LEFT JOIN ".TABLE_PREFIX."userfields f ON (f.ufid=u.uid)
		WHERE u.uid='{$uid}'
		LIMIT 1
	");
	$mybb->user = $db->fetch_array($query);
	if(!$mybb->user)
	{
		return false;
	}

	$mybbgroups = $mybb->user['usergroup'];
	if(!empty($mybb->user['additionalgroups']))
	{
		$mybbgroups .= ','.$mybb->user['additionalgroups'];
	}

	$mybb->usergroup = usergroup_permissions($mybbgroups);
	if(!$mybb->user['displaygroup'])
	{
		$mybb->user['displaygroup'] = $mybb->user['usergroup'];
	}

	$mydisplaygroup = usergroup_displaygroup($mybb->user['displaygroup']);
	if(is_array($mydisplaygroup))
	{
		$mybb->usergroup = array_merge($mybb->usergroup, $mydisplaygroup);
	}

	if(!$mybb->user['usertitle'])
	{
		$mybb->user['usertitle'] = $mybb->usergroup['usertitle'];
	}

	return true;
}
