from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.shortcuts import redirect
from django.core.cache import cache
from django.utils.html import format_html
from django.http import HttpResponse
import subprocess
import json
from .models import StoreSettings
from .utils import send_firebase_notification
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from admin_portal.models import CustomUser
from django.contrib import messages
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
            path("send-test-notification/", self.admin_site.admin_view(self.send_test_notification), name="send_test_notification"),
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
    def send_test_notification(self, request):
        """Send a test Firebase notification to a single token"""

        # Provide your Firebase token here manually
        token = "d3qa6NZ4RyaOBbwCYCmlMU:APA91bEeoBEp5nPM0Tc2HFrH2fJg9pvp55tDDsQtqLeNbIhpbr1hoIYDegPVpssHp3zPyhHbBWIy0oYvG50K5ia3u2u9f-ukwUon6QcuW9fPvts5Ry-AShk"

        title = "🚀 Test Notification"
        body = "This is a test push notification from Django Admin"

        response = send_firebase_notification(title, body, token)
        if isinstance(response, dict) and "error" in response:  # If response is an error dict
            self.message_user(request, f"Failed to send notification: {response['error']}", level=messages.ERROR)
        else:
             self.message_user(request, f"Test notification sent successfully! Message ID: {response}")

        return redirect(request.META.get('HTTP_REFERER', '/admin/settings/storesettings/1/change/'))
    def render_change_form(self, request, context, *args, **kwargs):
        """Inject custom buttons into the Django admin form"""
        context["extra_buttons"] = mark_safe(f"""
            <div style="margin:20px 0;">
                <a href="/admin/settings/clear-cache/" class="button" style="background:#d9534f; color:white; padding:8px 16px; border-radius:4px; text-decoration:none;">Clear Cache</a>
                <a href="/admin/settings/backup-database/" class="button" style="background:#5bc0de; color:white; padding:8px 16px; border-radius:4px; text-decoration:none;">Backup Database</a>
                <a href="/admin/settings/send-test-notification/" class="button" style="background:#5cb85c; color:white; padding:8px 16px; border-radius:4px; text-decoration:none;">Send Test Notification</a>
            </div>
        """)
        return super().render_change_form(request, context, *args, **kwargs)