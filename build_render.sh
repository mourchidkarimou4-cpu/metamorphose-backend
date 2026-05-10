#!/usr/bin/env bash
set -e
echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt
echo "=== Collectstatic ==="
python manage.py collectstatic --noinput
echo "=== Migrations ==="
python manage.py migrate
echo "=== Build terminé ==="
