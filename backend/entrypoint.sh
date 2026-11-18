#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_ingredients
python manage.py load_demo_data
python manage.py create_admin

exec "$@"
