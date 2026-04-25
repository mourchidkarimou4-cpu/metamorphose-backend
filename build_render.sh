#!/usr/bin/env bash
set -e

echo "=== Installation des dépendances Python ==="
pip install -r requirements.txt

echo "=== Build du frontend React ==="
# Installer Node via nvm (disponible sur Render)
export NVM_DIR="$HOME/.nvm"
if [ ! -d "$NVM_DIR" ]; then
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
fi
source "$NVM_DIR/nvm.sh"
nvm install 20
nvm use 20

# Cloner et builder le frontend
FRONTEND_DIR="/tmp/metamorphose-frontend"
if [ -d "$FRONTEND_DIR" ]; then
  rm -rf "$FRONTEND_DIR"
fi
git clone --depth 1 --branch main https://github.com/mourchidkarimou4-cpu/metamorphose-frontend.git "$FRONTEND_DIR"
cd "$FRONTEND_DIR"
npm install
VITE_API_URL="" npm run build

echo "=== Copie du build vers Django ==="
cd /opt/render/project/src
mkdir -p frontend/dist
cp -r "$FRONTEND_DIR/dist/." frontend/dist/
# Copier les icônes PWA
mkdir -p frontend/dist/icons
cp -r "$FRONTEND_DIR/public/icons/." frontend/dist/icons/

echo "=== Migrations Django ==="
python manage.py migrate

echo "=== Collectstatic ==="
python manage.py collectstatic --noinput

echo "=== Build terminé ==="
