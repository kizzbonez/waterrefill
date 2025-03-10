from django.contrib import admin
from .models import Product
from django.http import HttpResponse
import openpyxl
from django.utils.translation import gettext_lazy as _
from common import common
from django.urls import reverse
from django.utils.html import format_html
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_formatted_amount', 'stock', 'created_at', 'status','view_sales_history')  # Columns shown in admin list view
    search_fields = ('name',)  # Enables search by product name
    list_filter = ( ('created_at', admin.DateFieldListFilter), 'status')  # Removed `get_formatted_amount`
    ordering = ('-created_at', 'name', 'price', 'stock', 'status')  # Use `price` instead of `get_formatted_amount`
    actions = ["export_to_excel"]  # Add the export action

    # ✅ Exclude "cost", "weight", and "is_water_product"
    exclude = ('cost', 'weight', 'water_product')
    def view_sales_history(self, obj):
        """Generate a link to order details filtered by the product"""
        url = reverse('admin:orders_orderdetails_changelist') + f"?product__id__exact={obj.id}"
        return format_html(f'<a href="{url}" target="_blank">View Sales</a>')

    view_sales_history.short_description = "Sales History"
    def has_delete_permission(self, request, obj=None):
        """Disables delete option for all products"""
        return False

    @admin.display(ordering='price', description="price")  # Enables sorting and renames column
    def get_formatted_amount(self, obj):
        return common.formatted_amount(obj.price)  # Use the function from common.py

    def export_to_excel(self, request, queryset):
        """Exports selected products to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Product Data"

        headers = ["ID", "Name", "Description", "Price", "Stocks", "Status"]
        ws.append(headers)  # Add headers

        for product in queryset:
            ws.append([
                product.id,
                product.name,
                product.description,
                product.price,
                product.stock,
                product.status
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="product_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected Products to Excel"
