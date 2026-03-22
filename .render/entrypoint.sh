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

mkdir -p /var/www/html/cache/themes /var/www/html/uploads/avatars
chown -R www-data:www-data /var/www/html/cache /var/www/html/uploads /var/www/html/inc
chmod 775 /var/www/html/cache /var/www/html/cache/themes /var/www/html/uploads /var/www/html/uploads/avatars
chmod 664 /var/www/html/inc/config.php /var/www/html/inc/settings.php

exec "$@"
