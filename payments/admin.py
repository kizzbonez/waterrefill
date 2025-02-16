from django.contrib import admin
from django.utils.html import format_html
from .models import Payment
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from settings.models import StoreSettings
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'ref_code', 'status', 'payment_method', 'formatted_amount', 'proof', 'created_at')
    search_fields = ('ref_code', 'amount')
    list_filter = (
        ('created_at', admin.DateFieldListFilter),  # Adds a basic date filter
        'payment_method',
        'amount'
    ) 

    ordering = ('-created_at',)  
    actions = ["export_to_excel"]  #  Add the export action
    def formatted_amount(self, obj):
        store_settings = StoreSettings.objects.first()
        """Format amount as Philippine Pesos with thousand separators."""
        try:
            total_price = float(obj.amount) or 0  # Ensure the value is a number
            return f"{store_settings.currency_symbol}{total_price:,.2f}"  # Formats with Peso symbol and two decimal places
        except (ValueError, TypeError):
            return "Invalid Amount"

    formatted_amount.short_description = "Amount ({store_settings.currency_symbol})"  # Renames column in admin panel

    def export_to_excel(self, request, queryset):
        """Exports selected payments to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Payment Data"

        headers = ["ID", "REF code", "Amount", "Payment Method", "Status","Order ID",  "Payment Date"]
        ws.append(headers)  # Add headers

        for payment in queryset:
            ws.append([
                payment.id,
                payment.ref_code,
                payment.amount,
                payment.get_payment_method_display(),
                payment.get_status_display(),
                payment.order_id.__str__() if payment.order_id else "No Order",
                payment.created_at.replace(tzinfo=None) if  payment.created_at else None
              
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="payment_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected Products to Excel"

