from pathlib import Path
from datetime import timedelta
import os
from decouple import config as env_config

BASE_DIR = Path(__file__).resolve().parent.parent

# ── SÉCURITÉ ───────────────────────────────────────────────────
SECRET_KEY = env_config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG      = env_config('DEBUG', default='True', cast=bool)
ALLOWED_HOSTS = env_config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ── APPLICATIONS ───────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'cloudinary_storage',
    'cloudinary',
    'channels',
    'live',
    'rest_framework_simplejwt',
    'corsheaders',
    'accounts',
    'contenu',
    'administration',
    'cadeaux',
    'avis',
    'paiement',
    'learning',
    'tickets',
]

# ── MIDDLEWARE ─────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF    = 'config.urls'
AUTH_USER_MODEL = 'accounts.CustomUser'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── BASE DE DONNÉES ────────────────────────────────────────────
DATABASE_URL = env_config('DATABASE_URL', default='')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── DRF + JWT ──────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '3000/hour',
        'agent_ia': '30/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# ── CORS ───────────────────────────────────────────────────────
_cors_env = env_config('CORS_ALLOWED_ORIGINS', default='http://localhost:5173,http://localhost:3000')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(',')]
CORS_ALLOWED_ORIGINS += ['http://10.32.78.12:5173']
CORS_ALLOW_CREDENTIALS = True

# ── FICHIERS STATIQUES & MEDIA ─────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# ── SÉCURITÉ HTTPS (prod uniquement) ──────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT         = True
    SECURE_PROXY_SSL_HEADER     = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS         = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE       = True
    CSRF_COOKIE_SECURE          = True
    CSRF_TRUSTED_ORIGINS        = ["https://metamorphose-frontend.vercel.app"]
    SECURE_BROWSER_XSS_FILTER   = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS             = 'DENY'

# ── INTERNATIONALISATION ───────────────────────────────────────
LANGUAGE_CODE     = 'fr-fr'
TIME_ZONE         = 'Africa/Porto-Novo'
USE_I18N          = True
USE_TZ            = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CHANNELS (WebSocket) ────────────────────────────────────────
ASGI_APPLICATION = 'config.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── EMAIL ──────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = env_config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env_config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = env_config('DEFAULT_FROM_EMAIL', default='Méta\'Morph\'Ose <contact@metamorphose.com>')
ADMIN_EMAIL         = env_config('EMAIL_HOST_USER', default='')

# ── CLOUDINARY ─────────────────────────────────────────────────
import cloudinary
cloudinary.config(
    cloud_name = env_config('CLOUDINARY_CLOUD_NAME', default=''),
    api_key    = env_config('CLOUDINARY_API_KEY',    default=''),
    api_secret = env_config('CLOUDINARY_API_SECRET', default=''),
    secure     = True,
)

FRONTEND_URL = env_config('FRONTEND_URL', default='https://metamorphose-frontend.vercel.app')

# ── FEDAPAY ────────────────────────────────────────────────────
FEDAPAY_SECRET_KEY     = env_config('FEDAPAY_SECRET_KEY',     default='')
FEDAPAY_WEBHOOK_SECRET = env_config('FEDAPAY_WEBHOOK_SECRET', default='')
FEDAPAY_ENV            = env_config('FEDAPAY_ENV',            default='sandbox')

# ── KKIAPAY ────────────────────────────────────────────────────
KKIAPAY_PUBLIC_KEY  = env_config('KKIAPAY_PUBLIC_KEY',  default='')
KKIAPAY_PRIVATE_KEY = env_config('KKIAPAY_PRIVATE_KEY', default='')
KKIAPAY_SECRET_KEY  = env_config('KKIAPAY_SECRET_KEY',  default='')
KKIAPAY_SANDBOX     = env_config('KKIAPAY_SANDBOX',     default='True', cast=bool)


# ── LOGGING ────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts':       {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'contenu':        {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'administration': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'avis':           {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'paiement':       {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}




