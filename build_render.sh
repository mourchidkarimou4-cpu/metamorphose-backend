#!/usr/bin/env bash
set -e
echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt
echo "=== Migrations Django ==="
python manage.py migrate
echo "=== Collectstatic ==="
python manage.py collectstatic --noinput
echo "=== Build terminé ==="
