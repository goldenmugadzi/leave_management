from .settings import *  # noqafrom pathlib import Path



# Test-only overrides# Minimal settings for tests

DEBUG = TrueBASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'test-secret-key'SECRET_KEY = 'test-secret-key'

DEBUG = True

# Use in-memory SQLite for speedALLOWED_HOSTS = ['*']

DATABASES = {

    'default': {INSTALLED_APPS = [

        'ENGINE': 'django.db.backends.sqlite3',    'django.contrib.admin',

        'NAME': ':memory:',    'django.contrib.auth',

    }    'django.contrib.contenttypes',

}    'django.contrib.sessions',

    'django.contrib.messages',

# Faster password hashing    'django.contrib.staticfiles',

PASSWORD_HASHERS = [    'rest_framework',

    'django.contrib.auth.hashers.MD5PasswordHasher',    'it.users',

]    'Asset_Register',

    'approve',

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'    'ACE2',

    'finance.PettyCash',

# Disable Prometheus middleware during tests to reduce noise (optional)]

MIDDLEWARE = [m for m in MIDDLEWARE if 'Prometheus' not in m]

MIDDLEWARE = [

# Speed up token lifetimes for tests if needed    'django.middleware.security.SecurityMiddleware',

SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=5)  # noqa: F405    'django.contrib.sessions.middleware.SessionMiddleware',

SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(minutes=10)    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

# Avoid external BASE_URL reliance if not set    'django.contrib.auth.middleware.AuthenticationMiddleware',

BASE_URL = 'http://testserver'    'django.contrib.messages.middleware.MessageMiddleware',

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

# Static/media paths (in-memory / temp not required but keep consistent)

ROOT_URLCONF = 'beii_v1.test_urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'beii_v1.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

AUTH_USER_MODEL = 'users.UserProfile'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Disable migrations for apps to simplify test DB setup
MIGRATION_MODULES = {
    'ACE2': None,
    'approve': None,
    'users': None,
    'Asset_Register': None,
    'PettyCash': None,
}
