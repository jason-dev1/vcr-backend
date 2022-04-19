from decouple import config
from .common import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '192.168.68.100']

SECRET_KEY = 'django-insecure-*g_x6+ingy0x*0evk^np(wn@bj79kjh@f11rzq_(0t52-9)2*l'

INTERNAL_IPS = [
    "127.0.0.1",
    '192.168.68.100'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'vcr',
        'USER': config('DEV_DB_USER', default='postgres'),
        'PASSWORD': config('DEV_DB_PASSWORD', default='PASSWORD'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
    'osm': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'osm',
        'USER': config('DEV_DB_USER', default='postgres'),
        'PASSWORD': config('DEV_DB_PASSWORD', default='PASSWORD'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
}
