import os
from .common import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['vcr-django.herokuapp.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'vcr',
        'USER': os.environ['PROD_DB_USER'],
        'PASSWORD': os.environ['PROD_DB_PASSWORD'],
        'HOST': os.environ['PROD_DB_HOST'],
        'PORT': '5432',
    },
    'osm': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'osm',
        'USER': os.environ['PROD_DB_USER'],
        'PASSWORD': os.environ['PROD_DB_PASSWORD'],
        'HOST':  os.environ['PROD_DB_HOST'],
        'PORT': '5432',
    }
}
