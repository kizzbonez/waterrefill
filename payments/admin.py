from django.contrib import admin
from django.utils.html import format_html
from .models import Payment
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from settings.models import StoreSettings
from common import common
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'ref_code', 'status', 'payment_method', 'get_formatted_amount', 'proof', 'created_at')
    search_fields = ('ref_code', 'amount')
    list_filter = (
        ('created_at', admin.DateFieldListFilter),  # Adds a basic date filter
        'payment_method',
        'amount'
    ) 

    ordering = ('-created_at','-order_id','status','amount')  
    actions = ["export_to_excel"]  #  Add the export action
    @admin.display(ordering='amount', description="Amount")  # Enables sorting and renames column
    def get_formatted_amount(self, obj):
        return common.formatted_amount(obj.amount)  # Use the function from common.py

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

