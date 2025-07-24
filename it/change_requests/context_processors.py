# utils/context_processors.py
from django.conf import settings
from decouple import config

def environment_vars(request):
    return {
        'DEBUG': config('DEBUG', default=False, cast=bool),
        'HOST': config('HOST', default='localhost'),
        'PORT': config('PORT', default='8000'),
        'ENVIRONMENT': config('ENVIRONMENT', default='development'),
        'VERSION': config('VERSION', default='1.0.0'),
    }

def captcha_context(request):
    """Make reCAPTCHA site key available in templates"""
    return {
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_PUBLIC_KEY,
        'RECAPTCHA_ENABLED': getattr(settings, 'RECAPTCHA_ENABLED', True)
    }