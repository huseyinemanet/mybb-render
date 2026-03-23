<?php
/**
 * Local router for PHP built-in server.
 * Mirrors Google SEO rewrite rules that .htaccess handles on Apache.
 */

$rawUri = $_SERVER['REQUEST_URI'] ?? '/';
$rawPath = parse_url($rawUri, PHP_URL_PATH) ?? '/';
if (preg_match('#^//+#', $rawUri) || preg_match('#^//+#', $rawPath)) {
    $normalized = preg_replace('#^//+#', '/', $rawUri);
    header('Location: ' . $normalized, true, 301);
    exit;
}

$uriPath = urldecode($rawPath);
$fullPath = __DIR__ . $uriPath;

if ($uriPath !== '/' && is_file($fullPath)) {
    return false;
}

if (preg_match('#^/(?:thread|forum|user|announcement|calendar|event)/([A-Za-z0-9_]+)\.php$#u', $uriPath, $m)) {
    $candidate = strtolower($m[1]) . '.php';
    if (is_file(__DIR__ . '/' . $candidate)) {
        $dest = '/' . $candidate;
        $qs = $_SERVER['QUERY_STRING'] ?? '';
        if ($qs !== '') {
            $dest .= '?' . $qs;
        }
        header('Location: ' . $dest, true, 301);
        exit;
    }
}

if (preg_match('#^/(?:thread|forum|user|announcement|calendar|event)/(images|jscripts|uploads|cache)/(.+)$#iu', $uriPath, $m)) {
    $assetPath = __DIR__ . '/' . $m[1] . '/' . $m[2];
    if (is_file($assetPath)) {
        $ext = strtolower(pathinfo($assetPath, PATHINFO_EXTENSION));
        $mime = [
            'png' => 'image/png',
            'jpg' => 'image/jpeg',
            'jpeg' => 'image/jpeg',
            'gif' => 'image/gif',
            'webp' => 'image/webp',
            'svg' => 'image/svg+xml',
            'css' => 'text/css; charset=utf-8',
            'js' => 'application/javascript; charset=utf-8',
            'woff' => 'font/woff',
            'woff2' => 'font/woff2',
            'ttf' => 'font/ttf',
        ][$ext] ?? 'application/octet-stream';
        header('Content-Type: ' . $mime);
        readfile($assetPath);
        exit;
    }
}

$query = [];
parse_str($_SERVER['QUERY_STRING'] ?? '', $query);
$script = 'index.php';
$extra = [];

if (preg_match('#^/sitemap\-([^./]+)\.xml$#iu', $uriPath, $m)) {
    $script = 'misc.php';
    $extra = ['google_seo_sitemap' => $m[1]];
}

if (preg_match('#^/forum/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'forumdisplay.php';
    $extra = ['google_seo_forum' => $m[1]];
}

if (preg_match('#^/thread/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'showthread.php';
    $extra = ['google_seo_thread' => $m[1]];
}

if (preg_match('#^/announcement/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'announcements.php';
    $extra = ['google_seo_announcement' => $m[1]];
}

if (preg_match('#^/user/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'member.php';
    $extra = ['action' => 'profile', 'google_seo_user' => $m[1]];
}

if (preg_match('#^/calendar/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'calendar.php';
    $extra = ['google_seo_calendar' => $m[1]];
}

if (preg_match('#^/event/([^./]+)$#iu', $uriPath, $m)) {
    $script = 'calendar.php';
    $extra = ['action' => 'event', 'google_seo_event' => $m[1]];
}

$_GET = array_merge($extra, $query);
$_REQUEST = array_merge($_REQUEST ?? [], $_GET, $_POST ?? []);
$_SERVER['SEO_SUPPORT'] = '1';
$_SERVER['SCRIPT_NAME'] = '/' . $script;
$_SERVER['PHP_SELF'] = '/' . $script;
require __DIR__ . '/' . $script;
exit;
