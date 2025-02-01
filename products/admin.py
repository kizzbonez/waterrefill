from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at')  # Columns shown in admin list view
    search_fields = ('name',)  # Enables search by product name
    list_filter = ('created_at', 'price')  # Adds filters for admin
    ordering = ('-created_at',)  # Orders products by newest first
