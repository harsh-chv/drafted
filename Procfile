web: python manage.py migrate --noinput && python manage.py sync_socialapps && python manage.py collectstatic --noinput && gunicorn drafted.wsgi --bind 0.0.0.0:$PORT --timeout 120
