import os
import sys
from datetime import timedelta
from pathlib import Path

from decouple import config
from django.contrib.messages import constants as messages

# Example usage in settings.py
BASE_URL = config('BASE_URL')

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOWED_ORIGINS = [
#     config('BASE_URL') + ":" + config('PORT'),
#     config('BASE_URL') + ":3000",
# ]

# CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    config('BASE_URL'),
    config('BASE_URL') + ":" + config('PORT'),
    "https://6a436b963963.ngrok-free.app",
    # Add your production domain here
    # "https://your-production-domain.com"
]

CORS_ALLOW_HEADERS = ('content-disposition', 'accept-encoding',
                      'content-type', 'accept', 'origin', 'authorization')

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=100),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=10),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "it.users.serializers.MyTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

# Set session to expire after 30 minutes of inactivity
# SESSION_COOKIE_AGE = 100 * 60  # 30 minutes * 60 seconds

# Application definition
sys.path.insert(1, os.path.join(BASE_DIR, 'engineering'))
sys.path.insert(2, os.path.join(BASE_DIR, 'commercials'))
sys.path.insert(3, os.path.join(BASE_DIR, 'hr'))
sys.path.insert(4, os.path.join(BASE_DIR, 'reports'))
sys.path.insert(5, os.path.join(BASE_DIR, 'api/ops_maintenance'))
sys.path.insert(7, os.path.join(BASE_DIR, 'miscellaneous'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'clearcache',
    'risk.audit.nonconformity',
    'it.beii_auth',
    'it.users',
    'it.change_requests',
    'process_management',
    # 'executive.exec_dashboards',
    'executive.general_dashboards.apps.GeneralDashboardsConfig',
    'knowledge_center',
    'Docs',
    'approve',
    'processes.apps.ProcessesConfig',
    'process_risks.apps.ProcessRisksConfig',
    'finance.Ace',
    'finance.purchase_request',
    'finance.PettyCash',
    'finance.comparative_schedules',
    'finance.ristricted_bidding',
    'finance.direct_purchase',
    'finance.Direct_purchases',
    'ACE2',
    'esearch',
    'appraisal.apps.AppraisalConfig',

    'toolsandequipment',
    'fault_locator',
    'Transport',
    'Hardware_Faults',
    'Asset_Register',
    'register',
    'overtime',
    'asset_transfer',
    'widget_tweaks',
    'meetings',
    'leave_management',
    'reports',
    'sweetify',
    'mathfilters',
    'tokens',
    'commecial.tempertockens',
    'competence_building.apps.CompetenceBuildingConfig',
    'crispy_forms',
    'crispy_tailwind',
    'graphene_django',
    'graphene_file_upload',
    'safety',
    'BatteryMaintenance', 
    'comm_files',
    # 'django_prometheus',  # Temporarily disabled due to import error
    'api.ops_maintenance.safety_operations',
    'utils',
    'substation_inspections',
    'e60_inspections',
    'circuit_breaker_maintenance',
    'sanction_for_test',
    'inspections',
    'EquipTracker',
    'equipment_management',
    'pretask_risk_assessment',
]

AUTH_USER_MODEL = 'users.UserProfile'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'inspections.middleware.APIRequestLoggingMiddleware',  # API request logging
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'it.beii_auth.inactive_user_middleware.InactiveUserMiddleware',
    'it.beii_auth.session_middleware.LimitConcurrentSessionsMiddleware',
    'it.beii_auth.session_middleware.SessionErrorSessionMiddleware'
]

# ================= Appraisal Middleware ========================
MIDDLEWARE += [
    'appraisal.middleware.LoginRequiredForAppraisalMiddleware',
]

ROOT_URLCONF = 'beii_v1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'it.beii_auth.context_processors.environment_vars'
            ],
        },
    },
]

WSGI_APPLICATION = 'beii_v1.wsgi.application'
ASGI_APPLICATION = 'beii_v1.wsgi.application'
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', config('SECURE_PROXY_SSL_HEADER', default='https'))
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# Cookie Security
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
# CSRF cookie must be accessible to JavaScript for AJAX/React apps
# Reference: https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False

# Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME-type sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking attacks
SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS filtering
SECURE_REFERRER_POLICY = 'same-origin'  # Prevent referrer information leakage
X_ROBOTS_TAG = 'noindex, nofollow'  # Prevent search engine indexing

# Set session timeout to 10 minutes (600 seconds)
SESSION_COOKIE_AGE = 600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_LIMIT = 2
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASS'),
        'HOST': config('DB_HOST'),
    },
    # 'remote': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': config('REMOTE_DB_NAME'), 
    #     'USER': config('REMOTE_DB_USER'),
    #     'PASSWORD': config('REMOTE_DB_PASS'),
    #     'HOST': config('REMOTE_DB_HOST'),
    #     'PORT': config('REMOTE_DB_PORT', default='3306'),
    # }
}



GRAPHENE = {
    'SCHEMA': 'beii_v1.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'dashboard_formatter': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
        'performance_formatter': {
            'format': '{asctime} [PERFORMANCE] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': config('LOG_FILE', default='debug.log'),
            'formatter': 'verbose',
        },
        'dashboard_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('DASHBOARD_LOG_FILE', default='dashboard_enhancement.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'dashboard_formatter',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('PERFORMANCE_LOG_FILE', default='dashboard_performance.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 3,
            'formatter': 'performance_formatter',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('SECURITY_LOG_FILE', default='security.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'dashboard_enhancement': {
            'handlers': ['dashboard_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'dashboard_performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dashboard_security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'executive.general_dashboards': {
            'handlers': ['dashboard_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'it.change_requests.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

TIME_ZONE = 'Africa/Harare'
USE_TZ = True

# settings.py
EXCHANGE_SETTINGS = {
    'email': config('MS_EMAIL'),
    'password': config('MS_EMAIL'),
    'server': config('MS_SERVER'),
    'primary_smtp_address': config('MS_PRIMARY_SMTP_ADDRESS'),
}
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'perseychinaka@gmail.com'
# EMAIL_HOST_PASSWORD = 'apppassword'
# DEFAULT_FROM_EMAIL = "Zetdc Business Excellence "


# Emails
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_BACKEND = config('EMAIL_BACKEND')
# EMAIL_USE_TLS = True
Email_USE_SSL = True
EMAIL_HOST = config("MS_SERVER")
# EMAIL_PORT = config("EMAIL_PORT")
EMAIL_HOST_USER = config("MS_EMAIL")
DEFAULT_FROM_EMAIL = config("MS_EMAIL")
EMAIL_HOST_PASSWORD = config("MS_PASS")

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 30

LANGUAGE_CODE = 'en-us'

USE_I18N = True

LOGIN_REDIRECT_URL = '/dashboards/overview'
LOGIN_URL = '/accounts/login'

os.environ['TIKA_SERVER_JAR'] = os.path.join(BASE_DIR,'static','tika','tika-server-standard-2.9.2.jar')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "uploads", BASE_DIR / "media"]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/dashboards/overview'

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"
