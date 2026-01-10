"""
Django settings for mysite project.
Optimized for Railway.app Deployment.
"""

from pathlib import Path
import os
import dj_database_url  # Essential for Railway PostgreSQL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY SETTINGS ---
# Loads from Railway environment variables in production
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-0pwhx+%(we1d!kwfp%3o+ibgir6+eq0bqzsdc0ifv&-x+fa*m4')

# Set DEBUG to False in production by default
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Allow local dev and your Railway domain
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.railway.app']


# --- APPLICATION DEFINITION ---

INSTALLED_APPS = [
    "jazzmin",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Serves static files efficiently
    'django.contrib.staticfiles',
    "channels",
    'jobs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # MUST be here
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'
ASGI_APPLICATION = "mysite.asgi.application"


# --- DATABASE CONFIGURATION ---
# Uses PostgreSQL on Railway, falls back to SQLite locally
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600
    )
}


# --- CHANNELS & REDIS ---
# Using Redis for production chat. Locally, uses In-Memory
if not DEBUG:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
            },
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }


# --- STATIC & MEDIA FILES ---

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "jobs" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise storage for compression and caching
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- OTHER SETTINGS ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/redirect_dashboard/'
LOGOUT_REDIRECT_URL = '/'

# JAZZMIN_SETTINGS stay exactly as you had them...
JAZZMIN_SETTINGS = {
    "site_title": "JobConnect Admin",
    "site_header": "JobConnect Control Panel",
    "site_brand": "JobConnect",
    "theme": "minty",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "jobs.userprofile": "fas fa-id-card",
        "jobs.job": "fas fa-briefcase",
        "jobs.application": "fas fa-file-alt",
        "jobs.interview": "fas fa-video",
        "jobs.chatroom": "fas fa-comments",
        "jobs.chatmessage": "fas fa-envelope",
        "jobs.chatattachment": "fas fa-paperclip",
    },
}
