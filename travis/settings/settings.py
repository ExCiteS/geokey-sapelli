import os.path
from geokey.core.settings.dev import *

DEFAULT_FROM_EMAIL = 'sender@example.com'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'geokey',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS += (
    'geokey_sapelli',
)

STATIC_URL = '/static/'

MEDIA_ROOT = normpath(join(dirname(dirname(abspath(__file__))), 'assets'))
MEDIA_URL = '/assets/'

WSGI_APPLICATION = 'settings.wsgi.application'
ROOT_URLCONF = 'settings.urls'

SAPELLI_JAR = '../files/sapelli-collector-cmdln-2.0.0-beta-16-jar-with-dependencies.jar'
SAPELLI_CLIENT_ID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
