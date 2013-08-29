# Django settings for fantasy_football project.
import os
from yahoo_credentials import *
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'logs_dev'))

GOOGLE_SCOPE = ['https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/glass.timeline',
                'https://www.googleapis.com/auth/glass.location']

if os.environ.get('$OPENSHIFT_MYSQL_DB_HOST') is None:
    ENV = 'dev'
else:
    ENV = 'production'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
YAHOO_GAME_ID = 314
YAHOO_CACHE_PATH = os.path.join(PROJECT_ROOT, 'fantasy_football/cache/')
MANAGERS = ADMINS

# Decide production vs dev settings
if ENV == 'production':
    print "production"
    # TODO fix this to work for production settings.
    GOOGLE_REDIRECT_URI = 'https://scouteronglass.com/oauth/google/redirect/'
    DEBUG = False
    TEMPLATE_DEBUG = DEBUG
elif ENV == 'dev':


    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'ff',                      # Or path to database file if using sqlite3.
            'USER': 'root',                      # Not used with sqlite3.
            'PASSWORD': 'password',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
    GOOGLE_REDIRECT_URI = 'http://localhost:8000/oauth/google/redirect/'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

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

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'fantasy_football/static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1a7%lj7#3*e9#e2da_3^xojlo(o1=32t0t5ihqjm97mu8k#bw7'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'fantasy_football.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'fantasy_football.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, '../website/templates/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'south',
    'website'
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    'require_debug_false': {
    '()': 'django.utils.log.RequireDebugFalse'
    }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        # 'file_log': {                 # define and name a second handler
        #     'level': 'DEBUG',
        #     'class': 'logging.FileHandler',  # set the logging class to log to a file
        #     'formatter': 'verbose',         # define the formatter to associate
        #     'filename': os.path.join(PROJECT_ROOT, 'logs/output.log')  # log file
        # },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'website': {
            'handlers': [ 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'api': {
            'handlers': [ 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'views': {               # define another logger
            'handlers': ['console'],  # associate a different handler
            'level': 'DEBUG',                 # specify the logging level
            'propagate': True,
        },
    }
}

# Football specific
STAT_ID_MAP = {
    4: 'Pass Yds',
    5: 'Pass TD',
    6: 'Int',
    9: 'Rush Yds',
    10: 'Rush TD',
    12: 'Rec Yds',
    13: 'Rec TD',
    15: 'Ret TD',
    16: '2-PT',
    18: 'Fum Lost',
    57: 'Fum Ret TD',
    19: 'FG 0-19',
    20: 'FG 20-29',
    21: 'FG 30-39',
    22: 'FG 40-49',
    23: 'FG 50+',
    29: 'PAT Made',
    31: 'Pts Allow',
    32: 'Sack',
    33: 'Int',
    34: 'Fum Rec',
    35: 'TD',
    36: 'Safe',
    37: 'Blk Kick',
    49: 'Kick and Punt Ret TD',
    50: 'Pts Allow 0',
    51: 'Pts Allow 1-6',
    52: 'Pts Allow 7-13',
    53: 'Pts Allow 14-20',
    54: 'Pts Allow 21-27',
    55: 'Pts Allow 28-34',
    56: 'Pts Allow 35+',
}

STAT_NOTIFICATION_MINIMUMS = {
    4: 0,#'Pass Yds',
    5: 1,#'Pass TD',
    6: 1,#'Int',
    9: 0,#'Rush Yds',
    10: 1,#'Rush TD',
    12: 0,#'Rec Yds',
    13: 1,#'Rec TD',
    15: 1,#'Ret TD',
    16: 1,#'2-PT',
    18: 1,#'Fum Lost',
    57: 1,#'Fum Ret TD',
    19: 1,#'FG 0-19',
    20: 1,#'FG 20-29',
    21: 1,#'FG 30-39',
    22: 1,#'FG 40-49',
    23: 1,#'FG 50+',
    29: 1,#'PAT Made',
    31: 1,#'Pts Allow',
    32: 0,#'Sack',
    33: 1,#'Int',
    34: 1,#'Fum Rec',
    35: 1,#'TD',
    36: 1,#'Safe',
    37: 1,#'Blk Kick',
    49: 1,#'Kick and Punt Ret TD',
    50: 0,#'Pts Allow 0',
    51: 0,#'Pts Allow 1-6',
    52: 0,#'Pts Allow 7-13',
    53: 0,#'Pts Allow 14-20',
    54: 0,#'Pts Allow 21-27',
    55: 0,#'Pts Allow 28-34',
    56: 0,#'Pts Allow 35+',
}

TEAM_ABBREVIATIONS = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "OAK": "Oakland Raiders",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SD": "San Diego Chargers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "STL": "Saint Louis Rams",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Redskins",
    "WSH": "Washington Redskins",
}

TEAM_TO_EDITORIAL_TEAM_FULL_NAME = {
    'Falcons': 'Atlanta Falcons',
    'Bills': 'Buffalo Bills',
    'Bears': 'Chicago Bears',
    'Bengals': 'Cincinnati Bengals',
    'Browns': 'Cleveland Browns',
    'Cowboys': 'Dallas Cowboys',
    'Broncos': 'Denver Broncos',
    'Lions': 'Detroit Lions',
    'Packers': 'Green Bay Packers',
    'Titans': 'Tennessee Titans',
    'Colts': 'Indianapolis Colts',
    'Chiefs': 'Kansas City Chiefs',
    'Raiders': 'Oakland Raiders',
    'Rams': 'St. Louis Rams',
    'Dolphins': 'Miami Dolphins',
    'Vikings': 'Minnesota Vikings',
    'Patriots': 'New England Patriots',
    'Saints': 'New Orleans Saints',
    'Giants': 'New York Giants',
    'Jets': 'New York Jets',
    'Eagles': 'Philadelphia Eagles',
    'Cardinals': 'Arizona Cardinals',
    'Steelers': 'Pittsburgh Steelers',
    'Chargers': 'San Diego Chargers',
    '49ers': 'San Francisco 49ers',
    'Seahawks': 'Seattle Seahawks',
    'Buccaneers': 'Tampa Bay Buccaneers',
    'Redskins': 'Washington Redskins',
    'Panthers': 'Carolina Panthers',
    'Jaguars': 'Jacksonville Jaguars',
    'Ravens': 'Baltimore Ravens',
    'Texans': 'Houston Texans',
}

TEAM_ICONS = {
    "ARI": "cardinals.gif",
    "ATL": "falcons.gif",
    "BAL": "ravens.gif",
    "BUF": "bills.gif",
    "CAR": "panthers.gif",
    "CHI": "bears.gif",
    "CIN": "bengals.gif",
    "CLE": "browns.gif",
    "DAL": "cowboys.gif",
    "DEN": "broncos.gif",
    "DET": "lions.gif",
    "GB": "packers.gif",
    "HOU": "texans.gif",
    "IND": "colts.gif",
    "JAX": "jaguars.gif",
    "KC": "chiefs.gif",
    "MIA": "dolphins.gif",
    "MIN": "vikings.gif",
    "NE": "patriots.gif",
    "NO": "saints.gif",
    "NYG": "giants.gif",
    "NYJ": "jets.gif",
    "OAK": "raiders.gif",
    "PHI": "eagles.gif",
    "PIT": "steelers.gif",
    "SD": "chargers.gif",
    "SEA": "seahawks.gif",
    "SF": "49ers.gif",
    "STL": "rams.gif",
    "TB": "buccaneers.gif",
    "TEN": "titans.gif",
    "WAS": "redskins.gif",
}

