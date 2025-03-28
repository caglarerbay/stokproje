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

# Geliştirme aşamasında DEBUG True, production'da False yapmalısın.
DEBUG = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # Opsiyonel: 'rest_framework.authentication.SessionAuthentication',
    ],
}

# ALLOWED_HOSTS ayarını, AWS instance'ınızın public DNS'i ekledim.
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'DESKTOP-6L81PLG',
    '10.0.2.2',
    'ec2-16-171-15-250.eu-north-1.compute.amazonaws.com',
]

# Uygulama tanımlamaları
INSTALLED_APPS = [
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
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nuk.stoktakip@gmail.com'
EMAIL_HOST_PASSWORD = 'oxfyfitygatvxaga'
DEFAULT_FROM_EMAIL = 'nuk.stoktakip@gmail.com'

# Image upload için gerekli
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Firebase için (örnek)
FCM_API_KEY = 'your_firebase_api_key'

CORS_ALLOW_ALL_ORIGINS = True
