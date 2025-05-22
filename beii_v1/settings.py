from pathlib import Path
import sys, os
from datetime import timedelta
from django.contrib.messages import constants as messages
from decouple import config

# Example usage in settings.py
BASE_URL = config('BASE_URL')

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-7per#nouy422m0!hn0!ecb7ltnq#!^#g!2r5&%^5c%v(!ivv&a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

<<<<<<< HEAD
ALLOWED_HOSTS = [config('HOST'), "127.0.0.1", "172.16.29.32", "172.16.28.32", "172.16.8.99", "businessexcellence.zetdc.co.zw"]
=======
ALLOWED_HOSTS = [config('HOST'), "127.0.0.1", "172.16.29.32", "172.16.28.32", "172.16.8.99"]

ALLOWED_HOSTS = [config('HOST'), "127.0.0.1", "172.16.8.99", "172.16.28.32"]
>>>>>>> e2710261 (ddd)
CORS_ALLOWED_ORIGINS = [
    config('BASE_URL') + ":" + config('PORT'),
    config('BASE_URL'),
    "https://businessexcellence.zetdc.co.zw",
    "http://172.16.28.32:9300",
    config('BASE_URL') + ":3000",
]

# CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    config('BASE_URL'), 
    config('BASE_URL') + ":" + config('PORT'), 
    "https://businessexcellence.zetdc.co.zw",
    "http://172.16.28.32:9300"
]

CORS_ALLOW_HEADERS = ('content-disposition', 'accept-encoding',
                      'content-type', 'accept', 'origin', 'authorization')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
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
    'clearcache',
    'risk.audit.nonconformity',
    'it.beii_auth',
    'it.users',
    'it.change_requests',
    'executive.exec_dashboards',
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
    'Transport',
    'Hardware_Faults',
    'Asset_Register',
    'widget_tweaks',
    'reports',
    'sweetify',
    'mathfilters',
    'tokens',
    'commecial.tempertockens',
    'competence_building.apps.CompetenceBuildingConfig',
    'comm_files',
    'django_prometheus',
    'api.ops_maintenance.safety_operations',
]

AUTH_USER_MODEL = 'users.UserProfile'

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'it.beii_auth.inactive_user_middleware.InactiveUserMiddleware',
    'it.beii_auth.session_middleware.LimitConcurrentSessionsMiddleware',
    'it.beii_auth.session_middleware.SessionErrorSessionMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
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
                'it.beii_auth.context_processors.environment_vars',
                'it.beii_auth.context_processors.captcha_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'beii_v1.wsgi.application'
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', config('SECURE_PROXY_SSL_HEADER', default='http'))
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)

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
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': config('LOG_FILE', default='debug.log')
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

TIME_ZONE = 'Africa/Harare'
USE_TZ = False

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
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024  # 1GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100  # Reduce to 100MB for better handling
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100  # Add this setting (100MB)

# Add timeout settings for requests
REQUEST_TIMEOUT = 300  # 5 minutes

LANGUAGE_CODE = 'en-us'

USE_I18N = True

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login'

os.environ['TIKA_SERVER_JAR'] = os.path.join(BASE_DIR, 'static', 'tika', 'tika-server-standard-2.9.2.jar')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "uploads", BASE_DIR / "media"]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/dashboards/overview'

# Add RECAPTCHA settings
RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_SITE_KEY', default='your_site_key_here')
RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_SECRET_KEY', default='your_secret_key_here')
RECAPTCHA_ENABLED = False  # Set to False to disable reCAPTCHA temporarily
