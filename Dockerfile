FROM php:8.5-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libfreetype6-dev \
        libjpeg62-turbo-dev \
        libonig-dev \
        libpng-dev \
        libpq-dev \
        libwebp-dev \
        libzip-dev \
        unzip \
    && docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j"$(nproc)" gd mbstring mysqli pdo_pgsql pgsql zip \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

COPY . /var/www/html
COPY .render/entrypoint.sh /usr/local/bin/mybb-entrypoint

RUN chown -R www-data:www-data /var/www/html \
    && chmod +x /usr/local/bin/mybb-entrypoint \
    && chmod 775 /var/www/html/cache /var/www/html/cache/themes /var/www/html/uploads /var/www/html/uploads/avatars

ENV APACHE_DOCUMENT_ROOT=/var/www/html

ENTRYPOINT ["mybb-entrypoint"]
CMD ["apache2-foreground"]
