from django.apps import AppConfig


class NonconformityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk.audit.nonconformity'
    label = 'nonconformity'
