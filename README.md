# Méta'Morph'Ose — Guide de Déploiement

## Architecture

| Composant | Technologie | Service |
|-----------|------------|---------|
| Frontend | React 18 + Vite | Vercel ou Nginx |
| Backend | Django 5.2 + Daphne ASGI | Render ou VPS |
| Base de données | PostgreSQL | Render ou VPS |
| Médias | Cloudinary | cloud.cloudinary.com |
| Paiement | Kkiapay | kkiapay.me |
| Live/Visio | Zoom API | marketplace.zoom.us |
| Chatbot IA | Groq llama-3.3-70b | console.groq.com |

## Repos GitHub

- Frontend : https://github.com/mourchidkarimou4-cpu/metamorphose-frontend
- Backend : https://github.com/mourchidkarimou4-cpu/metamorphose-backend

---

## Variables d'environnement Backend (.env)

    SECRET_KEY=votre_secret_key_django
    DEBUG=False
    ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
    DATABASE_URL=postgresql://user:password@host:5432/dbname
    CLOUDINARY_CLOUD_NAME=dp7v6vlgs
    CLOUDINARY_API_KEY=votre_api_key
    CLOUDINARY_API_SECRET=votre_api_secret
    GROQ_API_KEY=votre_groq_api_key
    ZOOM_ACCOUNT_ID=votre_account_id
    ZOOM_S2S_CLIENT_ID=votre_client_id
    ZOOM_S2S_CLIENT_SECRET=votre_client_secret
    LIVEKIT_URL=wss://votre-projet.livekit.cloud
    LIVEKIT_API_KEY=votre_api_key
    LIVEKIT_API_SECRET=votre_api_secret
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_HOST_USER=votre@gmail.com
    EMAIL_HOST_PASSWORD=votre_app_password

## Variables d'environnement Frontend (.env)

    VITE_API_URL=https://votre-domaine-backend.com

---

## Option A — Vercel (Frontend) + Render (Backend)

### Frontend sur Vercel

1. Connecter le repo GitHub sur vercel.com
2. Framework : Vite
3. Build command : npm run build
4. Output directory : dist
5. Ajouter VITE_API_URL=https://votre-backend.onrender.com
6. Vercel rebuild automatiquement a chaque push

### Backend sur Render

1. Creer un Web Service sur render.com
2. Connecter le repo GitHub backend
3. Environment : Python
4. Build command : ./build_render.sh
5. Start command : daphne -b 0.0.0.0 -p $PORT config.asgi:application
6. Ajouter toutes les variables d'environnement
7. Creer une PostgreSQL Database et copier l'URL dans DATABASE_URL

---

## Option B — VPS Ubuntu 22.04

### 1. Installer les dependances

    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql postgresql-contrib certbot python3-certbot-nginx git

### 2. PostgreSQL

    sudo -u postgres psql
    CREATE DATABASE metamorphose;
    CREATE USER metamorphose_user WITH PASSWORD 'mot_de_passe';
    GRANT ALL PRIVILEGES ON DATABASE metamorphose TO metamorphose_user;
    \q

### 3. Backend Django

    git clone https://github.com/mourchidkarimou4-cpu/metamorphose-backend.git
    cd metamorphose-backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    nano .env
    python manage.py migrate
    python manage.py collectstatic --noinput
    python manage.py createsuperuser

### 4. Service systemd

Creer /etc/systemd/system/metamorphose.service :

    [Unit]
    Description=Meta'Morph'Ose Django ASGI
    After=network.target

    [Service]
    User=www-data
    WorkingDirectory=/chemin/vers/metamorphose-backend
    EnvironmentFile=/chemin/vers/metamorphose-backend/.env
    ExecStart=/chemin/vers/venv/bin/daphne -b 127.0.0.1 -p 8000 config.asgi:application
    Restart=always

    [Install]
    WantedBy=multi-user.target

    sudo systemctl daemon-reload
    sudo systemctl enable metamorphose
    sudo systemctl start metamorphose

### 5. Frontend React

    git clone https://github.com/mourchidkarimou4-cpu/metamorphose-frontend.git
    cd metamorphose-frontend
    npm install
    echo "VITE_API_URL=https://api.votre-domaine.com" > .env
    npm run build

### 6. Nginx

Creer /etc/nginx/sites-available/metamorphose :

    server {
        listen 80;
        server_name votre-domaine.com www.votre-domaine.com;
        root /chemin/vers/metamorphose-frontend/dist;
        index index.html;
        location / { try_files $uri $uri/ /index.html; }
        location /static/ { alias /chemin/vers/staticfiles/; }
    }

    server {
        listen 80;
        server_name api.votre-domaine.com;
        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        location /static/ { alias /chemin/vers/staticfiles/; }
    }

    sudo ln -s /etc/nginx/sites-available/metamorphose /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx

### 7. SSL Let's Encrypt

    sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com -d api.votre-domaine.com

---

## Configuration CORS apres changement de domaine

Dans config/settings.py mettre a jour :

    CORS_ALLOWED_ORIGINS = [
        "https://votre-domaine.com",
        "https://www.votre-domaine.com",
    ]
    ALLOWED_HOSTS = ['votre-domaine.com', 'api.votre-domaine.com']

---

## Services tiers

### Cloudinary
- Compte sur cloudinary.com
- Recuperer CLOUD_NAME, API_KEY, API_SECRET

### Kkiapay
- Compte sur kkiapay.me
- Recuperer cle publique et privee

### Zoom
- App Server-to-Server OAuth sur marketplace.zoom.us
- Activer scopes meeting:write:admin et meeting:read:admin
- Recuperer Account ID, Client ID, Client Secret

### Groq AI
- Compte sur console.groq.com
- Generer une API key

---

## Mise a jour du projet

    # Backend
    cd metamorphose-backend
    git pull
    source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py collectstatic --noinput
    sudo systemctl restart metamorphose

    # Frontend
    cd metamorphose-frontend
    git pull
    npm install
    npm run build

---

## Structure Backend

    config/          Settings, URLs, ASGI
    accounts/        Authentification JWT
    avis/            Temoignages texte/video/audio
    masterclass/     Masterclass + photos
    live/            Sessions live LiveKit
    zoom/            Zoom API
    aura/            Chatbot IA Groq
    paiement/        Kkiapay
    learning/        MMO Learning
    evenements/      Evenements et tickets
    cadeaux/         Cartes cadeaux QR
    communaute/      Communaute
    contenu/         CMS
    build_render.sh  Script build Render

---

Developpeur : Mourchid Karimou
Projet : Meta'Morph'Ose pour Prelia Apedo
Stack : React 18 + Django 5.2 + PostgreSQL + Cloudinary
