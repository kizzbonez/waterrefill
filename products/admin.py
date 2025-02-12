from django.contrib import admin
from .models import Product
from django.http import HttpResponse
import openpyxl
from django.utils.translation import gettext_lazy as _
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at')  # Columns shown in admin list view
    search_fields = ('name',)  # Enables search by product name
    list_filter = ( ('created_at', admin.DateFieldListFilter), 'price')  # Adds filters for admin
    ordering = ('-created_at',)  # Orders products by newest first
    actions = ["export_to_excel"]  #  Add the export action

    # Allow Admins to export user data
    def export_to_excel(self, request, queryset):
        """Exports selected products to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Product Data"

        headers = ["ID", "Name", "Description", "Price", "Costing", 
                   "Stocks"]
        ws.append(headers)  # Add headers

        for product in queryset:
            ws.append([
                product.id,
                product.name,
                product.description,
                product.price,
                product.cost,
                product.stock
              
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="product_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected Products to Excel"

