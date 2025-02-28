from django.contrib import admin
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.html import format_html
from .models import Payment
from django.http import HttpResponse
import openpyxl
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from settings.models import StoreSettings
from common import common
from django.core.exceptions import ValidationError
from django import forms
from django.urls import path
from django.http import JsonResponse
from orders.models import Order

class PaymentAdminForm(forms.ModelForm):
    amount_to_pay = forms.CharField(
        required=False, 
        disabled=True, 
        label="AMOUNT TO PAY", 
        widget=forms.TextInput(attrs={'style': 'font-weight: bold; color: red;'})
    )
    balance_amount = forms.CharField(
        required=False, 
        disabled=True, 
        label="BALANCE AMOUNT", 
        widget=forms.TextInput(attrs={'style': 'font-weight: bold; color: red;'})
    )

    class Meta:
        model = Payment
        fields = '__all__'

    def clean_order_id(self):
        """Ensure that Order ID is required"""
        order_id = self.cleaned_data.get('order_id')
        if not order_id:
            raise ValidationError("Order ID is required. Please select an order.")
        return order_id

    def clean(self):
        """Dynamically calculate Amount to Pay and Balance"""
        cleaned_data = super().clean()
        order = cleaned_data.get('order_id')
        amount_paid = cleaned_data.get('amount', 0)

        if order:
            total_order_amount = order.get_total_amount()  # Retrieve total order amount
            balance = total_order_amount - amount_paid

            # Assign calculated values to fields
            cleaned_data['amount_to_pay'] = f"{total_order_amount:.2f}"
            cleaned_data['balance_amount'] = f"{balance:.2f}"

        return cleaned_data

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm  # Use the custom form for validation
    list_display = (
        'order_id', 'ref_code', 'status', 'payment_method', 
        'get_amount_to_pay', 'get_formatted_amount', 'get_balance', 
        'proof', 'created_at'
    )
    search_fields = ('ref_code', 'amount')
    list_filter = (
        ('created_at', admin.DateFieldListFilter),
        'payment_method',
        'amount'
    ) 
    ordering = ('-created_at', '-order_id', 'status', 'amount')  
    actions = ["export_to_excel"]  #  Add the export action
    def get_queryset(self, request):
        """Annotate queryset to make Amount to Pay and Balance sortable"""
        qs = super().get_queryset(request).select_related('order_id')
        
        qs = qs.annotate(
            amount_to_pay=F('order_id__order_details__total_price'),
            balance=ExpressionWrapper(F('order_id__order_details__total_price') - F('amount'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )
        return qs

    def get_urls(self):
        """Add a custom URL to fetch order details dynamically"""
        urls = super().get_urls()
        custom_urls = [
            path('get-order-total/', self.get_order_total, name='get_order_total'),
        ]
        return custom_urls + urls

    def get_order_total(self, request):
        """AJAX endpoint to fetch the total amount for a selected order"""
        order_id = request.GET.get('order_id')
        if not order_id:
            return JsonResponse({'error': 'No order ID provided'}, status=400)

        try:
            order = Order.objects.get(id=order_id)
            total_amount = order.get_total_amount()
            return JsonResponse({'amount_to_pay': total_amount})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

    @admin.display(ordering='amount', description="Amount Paid")  
    def get_formatted_amount(self, obj):
        """Retrieve formatted amount paid"""
        return common.formatted_amount(obj.amount)  

    @admin.display(ordering='amount_to_pay', description="Amount to Pay")
    def get_amount_to_pay(self, obj):
        """Retrieve total order amount from annotated queryset"""
        return common.formatted_amount(obj.amount_to_pay) if obj.amount_to_pay else "N/A"

    @admin.display(ordering='balance', description="Balance")
    def get_balance(self, obj):
        """Retrieve balance from annotated queryset"""
        return common.formatted_amount(obj.balance) if obj.balance else "N/A"

    def export_to_excel(self, request, queryset):
        """Exports selected payments to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Payment Data"

        headers = ["ID", "REF Code", "Amount to Pay", "Amount Paid", "Balance", "Payment Method", "Status", "Order ID", "Payment Date"]
        ws.append(headers)

        for payment in queryset:
            total_order_amount = payment.amount_to_pay
            balance = payment.balance

            ws.append([
                payment.id,
                payment.ref_code,
                total_order_amount,
                payment.amount,
                balance,
                payment.get_payment_method_display(),
                payment.get_status_display(),
                payment.order_id.__str__() if payment.order_id else "No Order",
                payment.created_at.replace(tzinfo=None) if payment.created_at else None
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="payment_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected Payments to Excel"
