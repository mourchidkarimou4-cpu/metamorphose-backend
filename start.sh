#!/bin/bash
if [ "$LOAD_FIXTURES" = "true" ]; then
  echo "Loading fixtures (LOAD_FIXTURES=true)..."
  python manage.py loaddata fixtures/data.json --ignorenonexistent
  echo "Fixtures chargées."
fi
echo "Starting server..."
gunicorn config.wsgi:application
