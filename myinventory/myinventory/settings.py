"""
Django settings for myinventory project.

Generated by 'django-admin startproject' using Django 5.1.7.
"""

import os
from pathlib import Path

# Projenin ana dizini
BASE_DIR = Path(__file__).resolve().parent.parent

# Güvenlik için kullanılacak gizli anahtar (production'da değiştirmeyi unutma!)
SECRET_KEY = 'replace-this-with-a-very-secret-key'

# Geliştirme aşamasında DEBUG True olmalı, production'da False yapmalısın.
DEBUG = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # Opsiyonel: 'rest_framework.authentication.SessionAuthentication',
    ],
}



ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'DESKTOP-6L81PLG',
]

# Uygulama tanımlamaları
INSTALLED_APPS = [
    # Django'nun varsayılan uygulamaları
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'inventory',
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myinventory.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Global template klasörün varsa burada belirtebilirsin; yoksa APP_DIRS True olduğu için her uygulamanın template'leri okunur.
        'DIRS': [],
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

WSGI_APPLICATION = 'myinventory.wsgi.application'

# Veritabanı ayarları (SQLite kullanıyoruz)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Şifre doğrulama ayarları
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Dil ve zaman ayarları
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Statik dosyalar ayarı (CSS, JavaScript, resimler)
STATIC_URL = 'static/'

# Varsayılan otomatik alan tipi
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Giriş ve çıkış sonrası yönlendirme ayarları:
# Kullanıcı giriş yaptıktan sonra ana sayfaya yönlendir
LOGIN_REDIRECT_URL = '/'
# Kullanıcı çıkış yaptıktan sonra giriş (login) sayfasına yönlendir
LOGOUT_REDIRECT_URL = '/login/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nuk.stoktakip@gmail.com'
EMAIL_HOST_PASSWORD = 'oxfyfitygatvxaga'
DEFAULT_FROM_EMAIL = 'nuk.stoktakip@gmail.com'
CRITICAL_STOCK_ALERT_RECIPIENT = 'nuk.stoktakip@gmail.com'

# settings.py
FCM_API_KEY = 'your_firebase_api_key'

CORS_ALLOW_ALL_ORIGINS = True



