from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'

    def ready(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.db.utils import OperationalError, ProgrammingError

        try:
            # Create a dummy content type for the Reports model
            content_type, _ = ContentType.objects.get_or_create(
                app_label='reports',
                model='reports',  # lowercase model name
            )

            # Create the custom permission
            Permission.objects.get_or_create(
                codename='view_reports',
                name='Can view custom reports page',
                content_type=content_type,
            )

        except (OperationalError, ProgrammingError):
            # This can happen during initial migrations, so we safely ignore it
            pass
