import os
from .settings import *
from getenv import env


if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'travis_ci_test',
            'USER': 'postgres',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': os.getenv('PGPORT'),
        },
    }

    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': env('ELASTICSEARCH_TEST_HOST'),
            'http_auth': env('ELASTICSEARCH_TEST_AUTH'),
        },
    }
