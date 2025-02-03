from django.apps import AppConfig
from django.conf import settings

class SettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "settings"

    def ready(self):
        """Dynamically update JAZZMIN_SETTINGS after Django is ready"""
        from .models import StoreSettings

        store_settings = StoreSettings.objects.first()
        
        # Update Django settings at runtime
        settings.JAZZMIN_SETTINGS.update({
            "site_title": store_settings.store_name if store_settings else "Admin",
            "site_header": store_settings.store_name if store_settings else "Admin Dashboard",
            "site_brand": store_settings.store_name if store_settings else "My Store",
            "welcome_sign": f"Welcome to {store_settings.store_name}" if store_settings else "Welcome to Admin",
            "copyright": f"{store_settings.store_name} © 202" if store_settings else "My Store © 2024",
        })
      