import os
import json
import base64
from pathlib import Path
import firebase_admin
from firebase_admin import credentials
import dj_database_url

# ------------------------------
# 1. BASE DIRECTORY
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# 2. SECURITY SETTINGS
# ------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-local-secret-key")
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = ['*']

# ------------------------------
# 3. FIREBASE INITIALIZATION
# ------------------------------
firebase_base64 = os.environ.get("FIREBASE_KEY_BASE64")  # Base64-encoded JSON (optional)
firebase_json_path = os.path.join(BASE_DIR, "serviceAccountKey.json")  # Local dev

if not firebase_admin._apps:
    if firebase_base64:
        service_account_info = json.loads(base64.b64decode(firebase_base64))
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
    elif os.path.exists(firebase_json_path):
        cred = credentials.Certificate(firebase_json_path)
        firebase_admin.initialize_app(cred)
    else:
        print("WARNING: Firebase credentials not found! Firebase Auth will fail.")

# ------------------------------
# 4. APP DEFINITION
# ------------------------------
INSTALLED_APPS = [
    'jazzmin',  # Must be at top
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party
    'rest_framework',
    'corsheaders',

    # Local Apps
    'orders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# ------------------------------
# 5. TEMPLATES
# ------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ------------------------------
# 6. DATABASE
# -----------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('postgresql://eminence_eatz_db_user:xp6YDE7Sk44Gg5EARblwCbdx0Kj3N1nP@dpg-d6ps0rvgi27c73bfn7d0-a/eminence_eatz_db'),
        conn_max_age=600
    )
}

# ------------------------------
# 7. REST FRAMEWORK & CORS
# ------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'orders.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
CORS_ALLOW_ALL_ORIGINS = True

# ------------------------------
# 8. PAYSTACK KEYS
# ------------------------------
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY")
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_BASE_URL = "https://api.paystack.co"

# ------------------------------
# 9. STATIC & MEDIA
# ------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'




CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'otp_cache_table',
    }
}
# ------------------------------
# 10. EMAIL CONFIGURATION
# ------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# ------------------------------
# 11. JAZZMIN SETTINGS
# ------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "Eminence Eatz Admin",
    "site_header": "Eminence Eatz",
    "site_brand": "Eminence Eatz",
    "welcome_sign": "Welcome to Eminence Eatz HQ",
    "copyright": "Eminence Eatz Ltd",
    "search_model": "auth.User",
    "show_sidebar": True,
    "navigation_expanded": True,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/"},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "orders.Order": "fas fa-shopping-cart",
        "orders.Restaurant": "fas fa-store",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
}
