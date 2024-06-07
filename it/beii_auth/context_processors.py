# utils/context_processors.py
from decouple import config

def environment_vars(request):
    return {
        'DEBUG': config('DEBUG', default=False, cast=bool),
        'HOST': config('HOST', default='localhost'),
        'PORT': config('PORT', default='8000'),
    }