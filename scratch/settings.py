"""
Django settings for scratch project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sentry_sdk
from getenv import env
from sentry_sdk.integrations.django import DjangoIntegration
import ldap
from django_auth_ldap.config import LDAPSearch

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', 'secret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', False)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', env('ALLOWED_HOSTS')]

BASE_URL = env('BASE_URL', 'localhost:8000')

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()]
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'django_elasticsearch_dsl',
    'django_q',

    'app'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scratch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['app/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],

            'libraries': {
                'tags': 'app.tags.tags',
            }
        },
    },
]

WSGI_APPLICATION = 'scratch.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db',
        'PORT': 5432,
        'NAME': env('POSTGRES_DB', 'scratch'),
        'USER': env('POSTGRES_USER', 'scratch'),
        'PASSWORD': env('POSTGRES_PASSWORD', 'scratch'),
    }
}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env('ELASTICSEARCH_HOST'),
        'http_auth': env('ELASTICSEARCH_AUTH'),
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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


# REDIS
Q_CLUSTER = {
    'redis': {
        'host': env('REDIS_HOST', 'redis'),
        'port': int(env('REDIS_PORT', 6379)),
    }
}

# EMAIL
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', 'smtp')
EMAIL_PORT = env('EMAIL_PORT', 25)

# UNGM
UNGM_ENDPOINT_URI = env('UNGM_ENDPOINT_URI', 'https://www.ungm.org')

# TED
TED_FTP_URL = env('TED_FTP_URL', 'ted.europa.eu')
TED_FTP_USER = env('TED_FTP_USER', 'guest')
TED_FTP_PASSWORD = env('TED_FTP_PASSWORD', 'guest')
TED_DAYS_AGO = env('TED_DAYS_AGO', 3)
instance_dir = os.path.abspath(os.path.dirname(__file__))
FILES_DIR = os.path.join(instance_dir, 'files')

# DEADLINE
DEADLINE_NOTIFICATIONS = env('DEADLINE_NOTIFICATIONS', (1, 3, 7))

# TED
TED_DOC_TYPES = env('TED_DOC_TYPES', [])
TED_AUTH_TYPE = env('TED_AUTH_TYPE', '')


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "app/media")
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(os.path.join(BASE_DIR, "app"), 'static')
]
FIXTURE_DIRS = (
    '/app/fixtures/',
)

EMAIL_USE_TLS = env('EMAIL_USE_TLS', False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_SENDER = env('EMAIL_SENDER', '')

DELETE_EXPIRED_DAYS = env('DELETE_EXPIRED_DAYS', 5)

# LDAP
LDAP_HOST = env('LDAP_HOST', '')
LDAP_PORT = str(env('LDAP_PORT', ''))
LDAP_AUTH_USER_DN = env('LDAP_AUTH_USER_DN', '')

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
AUTH_LDAP_SERVER_URI = "ldap://" + ":".join((LDAP_HOST, LDAP_PORT))
AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    LDAP_AUTH_USER_DN, ldap.SCOPE_SUBTREE, "(uid=%(user)s)"
)
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "gecos",
    "email": "mail",
}

AUTH_LDAP_LOGIN_ATTEMPT_LIMIT = 100
AUTH_LDAP_RESET_TIME = 15 * 60
AUTH_LDAP_USERNAME_REGEX = r"^zz_.*$"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_ldap.backend.LDAPBackend',
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django_auth_ldap": {
            "level": "DEBUG", "handlers": ["console"]
        }
    }
}
