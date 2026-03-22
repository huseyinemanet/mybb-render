#!/bin/sh
set -eu

PORT_VALUE="${PORT:-10000}"

sed -i "s/Listen 80/Listen ${PORT_VALUE}/" /etc/apache2/ports.conf
sed -i "s/<VirtualHost \\*:80>/<VirtualHost *:${PORT_VALUE}>/" /etc/apache2/sites-available/000-default.conf

if [ ! -f /var/www/html/inc/config.php ]; then
  cp /var/www/html/.render/config.php.tpl /var/www/html/inc/config.php
fi

if [ ! -f /var/www/html/inc/settings.php ]; then
  cp /var/www/html/.render/settings.php.tpl /var/www/html/inc/settings.php
fi

db_ready="0"
if [ "${MYBB_DB_TYPE:-pgsql}" = "pgsql" ] && [ -n "${MYBB_DB_HOST:-}" ] && [ -n "${MYBB_DB_NAME:-}" ] && [ -n "${MYBB_DB_USER:-}" ]; then
  db_ready="$(
    php <<'PHP'
<?php
$host = getenv('MYBB_DB_HOST') ?: '';
$port = getenv('MYBB_DB_PORT') ?: '5432';
$name = getenv('MYBB_DB_NAME') ?: '';
$user = getenv('MYBB_DB_USER') ?: '';
$pass = getenv('MYBB_DB_PASSWORD') ?: '';
$prefix = getenv('MYBB_TABLE_PREFIX') ?: 'mybb_';

if ($host === '' || $name === '' || $user === '') {
    echo '0';
    exit;
}

try {
    $pdo = new PDO(
        sprintf('pgsql:host=%s;port=%s;dbname=%s', $host, $port, $name),
        $user,
        $pass,
        array(PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION)
    );
    $stmt = $pdo->prepare(
        "SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :table_name
        )"
    );
    $stmt->execute(array('table_name' => $prefix . 'datacache'));
    echo $stmt->fetchColumn() ? '1' : '0';
} catch (Throwable $e) {
    echo '0';
}
PHP
  )"
fi

if [ "$db_ready" = "1" ]; then
  : > /var/www/html/install/lock
else
  rm -f /var/www/html/install/lock
fi

mkdir -p /var/www/html/cache/themes /var/www/html/uploads/avatars
chown -R www-data:www-data /var/www/html/cache /var/www/html/uploads /var/www/html/inc
chmod 775 /var/www/html/cache /var/www/html/cache/themes /var/www/html/uploads /var/www/html/uploads/avatars
chmod 664 /var/www/html/inc/config.php /var/www/html/inc/settings.php

exec "$@"
