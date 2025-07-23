from django.apps import AppConfig


class SanctionForTestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sanction_for_test'
    verbose_name = 'Sanction For Test'

    def ready(self):
        import sanction_for_test.signals
    verbose_name = 'Sanction For Test'
    
    def ready(self):
        # Import signals here if needed
        pass
