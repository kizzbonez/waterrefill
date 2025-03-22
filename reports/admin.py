from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import Reports

class ReportsAdmin(admin.ModelAdmin):
    change_list_template = "admin/reports.html"  # ✅ Custom template

    def changelist_view(self, request, extra_context=None):
        return TemplateResponse(request, self.change_list_template, {
            **self.admin_site.each_context(request),
            "title": "Reports",
        })

admin.site.register(Reports, ReportsAdmin)
