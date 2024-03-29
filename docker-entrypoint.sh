#!/bin/sh

set -e

while ! nc -z db 5432; do
  echo "Waiting for PostgreSQL server at 5432 to accept connections on port 5432..."
  sleep 1s
done

if [ -z "$TIMEOUT" ]; then
    TIMEOUT=30
fi

if [ "x$DJANGO_MIGRATE" = 'xyes' ]; then
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_COLLECT_STATIC" = "xyes" ]; then
  python manage.py collectstatic --noinput
fi

if [ "x$DJANGO_INDEX_CONTENT" = "xyes" ]; then
  python manage.py search_index -f --rebuild
fi

if [ -z "$1" ]; then
  uwsgi uwsgi.ini
fi

python status/server.py

exec python manage.py $@
