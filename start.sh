#!/bin/bash
echo "Loading fixtures..."
python manage.py loaddata fixtures/data.json --ignorenonexistent
echo "Starting server..."
gunicorn config.wsgi:application
