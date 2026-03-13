import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials

# 1. BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. FIREBASE INITIALIZATION 
cred_path = os.path.join(BASE_DIR, 'serviceAccountKey.json')
if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print("WARNING: serviceAccountKey.json not found! Firebase Auth will fail.")

# 3. SECURITY SETTINGS
SECRET_KEY = 'django-insecure-t%9e=%@=6*(rh765lnw@3#8zii-zs)unh-!79+$4zi2*#t0cev'
DEBUG = False
ALLOWED_HOSTS = ['*'] 

# 4. APP DEFINITION
INSTALLED_APPS = [
    'jazzmin', # Must be at the top
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
    'corsheaders.middleware.CorsMiddleware', # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# 5. FIXED TEMPLATES SECTION
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True, # Required for Admin and Jazzmin
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

# 6. DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 7. REST FRAMEWORK & CORS
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'orders.authentication.FirebaseAuthentication', 
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
CORS_ALLOW_ALL_ORIGINS = True 

# 8. PAYSTACK KEYS
PAYSTACK_SECRET_KEY = "sk_test_f0248b82e35f065fe3b93ffcd0f2ad177eb2b530"
PAYSTACK_BASE_URL = "https://api.paystack.co"

# 9. STATIC & MEDIA
# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 10. EMAIL CONFIGURATION
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'danielkyerematengamartey@gmail.com' 
EMAIL_HOST_PASSWORD = 'zygs wvvv qrkk sjrt'

# 11. JAZZMIN SETTINGS
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
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
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