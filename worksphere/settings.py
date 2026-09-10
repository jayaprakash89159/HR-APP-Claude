"""
WorkSphere HR - Django Settings (Final Clean Version)
Uses os.environ only - avoids all URL parsing bugs
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'WorkSphereHR-Secret-Key-2025-Production-MinFiftyCharsRequired!!'
)
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,0.0.0.0,testserver,django,nginx,worksphere_django'
).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
    # Local - authentication MUST be before any app referencing auth_users
    'apps.authentication',
    'apps.employees',
    'apps.shifts',
    'apps.attendance',
    'apps.leave_management',
    'apps.workflow',
    'apps.payroll',
    'apps.notifications',
    'apps.audit',
    'apps.dashboard',
    'apps.hr_admin',
    'apps.reports',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'worksphere.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'apps.dashboard.context_processors.worksphere_settings',
        ],
    },
}]

WSGI_APPLICATION = 'worksphere.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME',     'worksphere_hr'),
        'USER':     os.environ.get('DB_USER',     'worksphere'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'worksphere123'),
        'HOST':     os.environ.get('DB_HOST',     'postgres'),
        'PORT':     os.environ.get('DB_PORT',     '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {'connect_timeout': 10},
    }
}

REDIS_URL = os.environ.get('REDIS_URL', 'redis://:worksphere123@redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'authentication.User'

AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = os.environ.get('TIME_ZONE', 'Asia/Kolkata')
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD  = 'django.db.models.BigAutoField'
LOGIN_URL           = '/auth/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.api.utils.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':        True,
    'ALGORITHM':                'HS256',
    'AUTH_HEADER_TYPES':        ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS  = True
CORS_ALLOW_CREDENTIALS  = True

_csrf = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost,http://localhost:8000,http://127.0.0.1:8000'
)
CSRF_TRUSTED_ORIGINS = [x.strip() for x in _csrf.split(',') if x.strip()]

CELERY_BROKER_URL      = os.environ.get('CELERY_BROKER_URL',    'redis://:worksphere123@redis:6379/1')
CELERY_RESULT_BACKEND  = os.environ.get('CELERY_RESULT_BACKEND','redis://:worksphere123@redis:6379/2')
CELERY_ACCEPT_CONTENT   = ['json']
CELERY_TASK_SERIALIZER  = 'json'
CELERY_RESULT_SERIALIZER= 'json'
CELERY_TIMEZONE         = TIME_ZONE
CELERY_BEAT_SCHEDULER   = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_TRACK_STARTED = True

EMAIL_BACKEND       = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS       = True
DEFAULT_FROM_EMAIL  = 'noreply@worksphere.hr'

SPECTACULAR_SETTINGS = {
    'TITLE':       'WorkSphere HR API',
    'DESCRIPTION': 'Enterprise HRMS Platform',
    'VERSION':     '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# HTTP-safe security (no SSL required)
SECURE_SSL_REDIRECT   = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE    = False
X_FRAME_OPTIONS       = 'SAMEORIGIN'

WORKSPHERE = {
    'COMPANY_NAME':    os.environ.get('COMPANY_NAME', 'WorkSphere HR'),
    'COMPANY_WEBSITE': os.environ.get('COMPANY_WEBSITE', 'http://localhost'),
    'SUPPORT_EMAIL':   'support@worksphere.hr',
    'CURRENCY_SYMBOL': '₹',
    'WORKING_HOURS_PER_DAY':   8,
    'WORKING_DAYS_PER_WEEK':   5,
    'ATTENDANCE_GRACE_PERIOD': 15,
    'GEO_FENCE_RADIUS':        300,
    'FINANCIAL_YEAR_START_MONTH': 4,
    'MAX_FILE_UPLOAD_SIZE': 10 * 1024 * 1024,
    'ALLOWED_FILE_TYPES': ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'],
}

# Intentionally empty by default. Configure jurisdiction-specific payroll
# rules per deployment; the payroll engine never invents statutory rates.
PAYROLL_STATUTORY_RULES = {}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django':    {'handlers': ['console'], 'level': 'INFO',    'propagate': False},
        'django.db': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
