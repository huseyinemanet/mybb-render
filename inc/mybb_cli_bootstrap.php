<?php
/**
 * MyBB bootstrap for CLI automation (after IN_MYBB, NO_ONLINE, THIS_SCRIPT are set).
 * Caller must chdir(MYBB root) before including this file.
 */

if(!defined('IN_MYBB'))
{
	define('IN_MYBB', 1);
}
if(!defined('NO_ONLINE'))
{
	define('NO_ONLINE', 1);
}
if(!defined('NO_PLUGINS'))
{
	define('NO_PLUGINS', 1);
}

if(!isset($_SERVER['REQUEST_METHOD']))
{
	$_SERVER['REQUEST_METHOD'] = 'GET';
}
if(!isset($_SERVER['HTTP_HOST']))
{
	$_SERVER['HTTP_HOST'] = 'localhost';
}
if(!isset($_SERVER['REQUEST_URI']))
{
	$_SERVER['REQUEST_URI'] = '/';
}
if(!isset($_SERVER['PHP_SELF']))
{
	$_SERVER['PHP_SELF'] = '/scripts/cli.php';
}
if(empty($_SERVER['REMOTE_ADDR']))
{
	$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
}

require_once __DIR__.'/init.php';

// Surface SQL query + message in CLI (file settings.php forces errortypemedium=none).
$mybb->settings['errortypemedium'] = 'error';

$lang->set_language($mybb->settings['bblanguage']);
$lang->load('global');

if(empty($config['admin_dir']) || !is_dir(MYBB_ROOT.$config['admin_dir'].'/inc'))
{
	if(defined('STDERR'))
	{
		fwrite(STDERR, "Invalid admin_dir in inc/config.php\n");
	}
	exit(1);
}

require_once MYBB_ROOT.$config['admin_dir'].'/inc/functions.php';
require_once MYBB_ROOT.'inc/mybb_automation_user.php';
