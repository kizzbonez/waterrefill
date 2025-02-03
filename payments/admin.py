from django.contrib import admin
from django.utils.html import format_html
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'ref_code', 'status', 'payment_method', 'formatted_amount', 'proof', 'created_at')
    search_fields = ('ref_code', 'amount')  
    list_filter = ('created_at', 'payment_method', 'amount')  
    ordering = ('-created_at',)  

    def formatted_amount(self, obj):
        """Format amount as Philippine Pesos with thousand separators."""
        try:
            total_price = float(obj.amount) or 0  # Ensure the value is a number
            return f"₱{total_price:,.2f}"  # Formats with Peso symbol and two decimal places
        except (ValueError, TypeError):
            return "Invalid Amount"

    formatted_amount.short_description = "Amount (₱)"  # Renames column in admin panel
