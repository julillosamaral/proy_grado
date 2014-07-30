import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

#sys.path.insert(0, os.path.dirname(__file__))

# calculated paths for django and the site
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT   = os.path.dirname(os.path.realpath(__file__))

AUTH_REQUIRED = False # possible location for global configuration flag
DEBUG = True # If set to True, TAXII will not return TAXII Messages for internal server errors.
TEMPLATE_DEBUG = True
#APPEND_SLASH = True
#TEMP_DIR = os.path.join(SITE_ROOT, "tmp")


### TAXII APP Specific Configs ###
#CERT_EXPORT_LOCATION = os.path.join(SITE_ROOT, 'client_certs/all_certs.cer') # The file Apache uses to validate users

#MANAGERS = ADMINS

# TAXII is configured to use SQLLite by default. To change
# the database used by TAXII, see the Django documentation on
# databases: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     'taxii_db',
        'USER': 'stix',
        'PASSWORD': 'stix',
       # 'HOST': '192.168.2.17',  #'192.168.0.103',
        'HOST': '192.168.0.108',
        'PORT': '3306',
    }
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# List of finder classes that know how to find static files in
# various locations.
#STATICFILES_FINDERS = (
 #   'django.contrib.staticfiles.finders.FileSystemFinder',
  #  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
#)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'gjk*d)_-o2v5zr7!zr)^h2$1%fs&jp^q!_gnv8&x)d-*!87u0^'



MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taxii.middleware.ProcessExceptionMiddleware',
    #'django.contrib.auth.middleware.RemoteUserMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

#AUTHENTICATION_BACKENDS = (
#    'django.contrib.auth.backends.RemoteUserBackend',
#)


ROOT_URLCONF = 'TAXIIApplication.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'TAXIIApplication.wsgi.application'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'TAXIIApplication',
    'taxii',
    'rest_framework',
    'rest',
    'djcelery',
    'kombu.transport.django',
)

import djcelery
djcelery.setup_loader()
BROKER_URL = "django://"

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 10
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "DEBUG"

LOG_DIRECTORY = os.path.join(SITE_ROOT, "log")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(message)s'
        },
        'normal': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'normal': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_DIRECTORY, 'TAXIIApplication.log'),
        },
        'stdout': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },

    },
    'loggers': {
        'TAXIIApplication': {
            'handlers': ['normal','stdout'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'taxii': {
            'handlers': ['normal','stdout'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'rest': {
            'handlers': ['normal','stdout'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    }
}


#try:
#   from TAXIIApplication.settings_local import * # overwrite with local settings if settings_local.py exists
#except ImportError:
#   pass

# Set the taxii authentication required flag to AUTH_REQUIRED
# This is done after the settings_local import in case local settings
# override the AUTH_FLAG declared above. We do this to keep the
#import taxii.settings
#taxii.settings.AUTH_REQUIRED = AUTH_REQUIRED


