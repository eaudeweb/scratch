import os
from .settings import *

if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'travis',
            'USER': 'testuser',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': os.getenv('PGPORT'),
        },
}
