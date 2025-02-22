from django.contrib import admin
from .models import Product
from django.http import HttpResponse
import openpyxl
from django.utils.translation import gettext_lazy as _
from common import common

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_formatted_amount', 'stock', 'created_at', 'status')  # Columns shown in admin list view
    search_fields = ('name',)  # Enables search by product name
    list_filter = ( ('created_at', admin.DateFieldListFilter), 'status')  # Removed `get_formatted_amount`
    ordering = ('-created_at', 'name', 'price', 'stock', 'status')  # Use `price` instead of `get_formatted_amount`
    actions = ["export_to_excel"]  # Add the export action


    def has_delete_permission(self, request, obj=None):
        """Disables delete option for all products"""
        return False
    @admin.display(ordering='price', description="price")  # Enables sorting and renames column
    def get_formatted_amount(self, obj):
        return common.formatted_amount(obj.price)  # Use the function from common.py
    # Allow Admins to export user data
    def export_to_excel(self, request, queryset):
        """Exports selected products to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Product Data"

        headers = ["ID", "Name", "Description", "Price", "Costing", "Stocks","Status"]
        ws.append(headers)  # Add headers

        for product in queryset:
            ws.append([
                product.id,
                product.name,
                product.description,
                product.price,
                product.cost,
                product.stock.
                product.status
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="product_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected Products to Excel"
