from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.utils.html import format_html
from .models import StoreSettings


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "timezone", "favicon_preview")

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
        ]
        return custom_urls + urls

    def clear_cache(self, request):
        """Handle the cache clearing action"""
        cache.clear()
        self.message_user(request, "Cache cleared successfully!")
        return redirect("/admin/settings/storesettings/1/change/")

    def render_change_form(self, request, context, *args, **kwargs):
        """Manually inject 'Clear Cache' button inside Jazzmin's jazzy-actions"""
        clear_cache_button = format_html(
            '<a class="btn btn-warning" href="/admin/settings/clear-cache/" '
            'style="margin-top: 10px; display: inline-block;">'
            '<i class="fas fa-sync-alt"></i> Clear Cache</a>'
        )

        if "jazzy-actions" in context:
            context["jazzy-actions"] += clear_cache_button  # Inject into Jazzmin buttons
        else:
            context["jazzy-actions"] = clear_cache_button  # If empty, set manually

        return super().render_change_form(request, context, *args, **kwargs)
