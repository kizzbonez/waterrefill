from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.shortcuts import redirect
from django.core.cache import cache
from django.utils.html import format_html
from django.http import HttpResponse
import subprocess
from .models import StoreSettings

@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "timezone", "favicon_preview")
    change_form_template = "admin/settings/change_form.html"  # Set custom template

    def favicon_preview(self, obj):
        """Show favicon preview in Django Admin"""
        if obj.favicon:
            return format_html('<img src="{}" width="32" height="32" style="border-radius:4px;"/>', obj.favicon.url)
        return "-"
    
    favicon_preview.short_description = "Favicon Preview"

    def has_add_permission(self, request):
        """Prevent adding new instances"""
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the settings"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect the list view to the edit form (only one settings instance exists)"""
        settings = StoreSettings.get_instance()
        return redirect(f"/admin/settings/storesettings/{settings.pk}/change/")

    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path("clear-cache/", self.admin_site.admin_view(self.clear_cache), name="clear_cache"),
            path("backup-database/", self.admin_site.admin_view(self.backup_database), name="backup_database"),
        ]
        return custom_urls + urls

    def clear_cache(self, request):
        """Handle the cache clearing action"""
        cache.clear()
        self.message_user(request, "Cache cleared successfully!")
        return redirect(request.META.get('HTTP_REFERER', '/admin/settings/storesettings/1/change/'))

    def backup_database(self, request):
        """Handle the database backup action"""
        db_settings = settings.DATABASES["default"]
        backup_file = "backup.sql"

        try:
            if db_settings["ENGINE"] == "django.db.backends.postgresql":
                subprocess.run([
                    "pg_dump", "-U", db_settings["USER"], "-h", db_settings["HOST"], "-p", str(db_settings["PORT"]), 
                    "-d", db_settings["NAME"], "-f", backup_file
                ], check=True)
            elif db_settings["ENGINE"] == "django.db.backends.mysql":
                subprocess.run([
                    "mysqldump", "-u", db_settings["USER"], "-p" + db_settings["PASSWORD"], "-h", db_settings["HOST"], 
                    db_settings["NAME"], "--result-file=" + backup_file
                ], check=True)
            elif db_settings["ENGINE"] == "django.db.backends.sqlite3":
                subprocess.run(["cp", db_settings["NAME"], backup_file], check=True)
            else:
                raise ValueError("Unsupported database engine")

            with open(backup_file, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/sql")
                response["Content-Disposition"] = f'attachment; filename="{backup_file}"'
                return response
        except Exception as e:
            self.message_user(request, f"Error during backup: {e}", level="error")
            return redirect(request.META.get('HTTP_REFERER', '/admin/settings/storesettings/1/change/'))
