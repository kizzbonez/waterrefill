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
from django.db import models
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from decimal import Decimal
from django.contrib.admin import SimpleListFilter
from admin_portal.models import CustomUser
from django.contrib.admin.views.main import ChangeList
class RiderFullNameFilter(SimpleListFilter):
    title = _('Rider')
    parameter_name = 'rider'

    def lookups(self, request, model_admin):
        riders = CustomUser.objects.filter(user_type=1)
        return [(r.id, f"{r.last_name}, {r.first_name}") for r in riders]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(order_id__assigned_to__id=self.value())
        return queryset
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
    
    def __init__(self, *args, **kwargs):
        """Dynamically populate amount_to_pay based on the current Payment ID"""
        super().__init__(*args, **kwargs)
        
        if self.instance:  # Check if this is an existing payment
            obj = self.instance
            if self.instance.order_id:
                # Retrieve total amount from the order model
                previousPayment = Payment.objects.filter(order_id=obj.order_id, created_at__lt=obj.created_at).aggregate(Sum('amount'))['amount__sum'] or 0
                amount_to_pay = obj.amount_to_pay - previousPayment 
                self.fields['amount_to_pay'].initial = f"{amount_to_pay}"
                self.fields['balance_amount'].initial = f"{amount_to_pay - obj.amount}"

    class Meta:
        model = Payment
        fields = '__all__'
    class Media:
        js = ('admin/js/balance_1.js',)  # Load the JavaScript file

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
        ('created_at', DateRangeFilter),
        'payment_method',
        'status',
        RiderFullNameFilter,
        'amount'
    ) 
    ordering = ('-created_at', '-order_id', 'status', 'amount')  
    actions = ["export_to_excel"]  #  Add the export action
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Get the changelist instance
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data['cl']  # ChangeList instance
            queryset = cl.queryset
            total_paid = queryset.aggregate(total=models.Sum('amount'))['total'] or 0
            extra_context['total_paid'] = common.formatted_amount(total_paid)
            response.context_data.update(extra_context)
        except (AttributeError, KeyError):
            print("Error")
            pass

        return response
    def has_delete_permission(self, request, obj=None):
        """Disables delete option for all products"""
        return False
    def has_change_permission(self, request, obj=None):
        """Disables delete option for all products"""
        if obj is None:
         return False  # Prevent deletion if no specific object is provided
        # Check if the product is in any order
        if obj.status == 1:
            return False
        return True
    def get_queryset(self, request):
        """Annotate queryset to make Amount to Pay and Balance sortable"""
        qs = super().get_queryset(request).select_related('order_id')

        # Aggregate total_price from order_details
        qs = qs.annotate(
            amount_to_pay=Sum('order_id__order_details__total_price'),  # Aggregate sum
            balance=ExpressionWrapper(
                Sum('order_id__order_details__total_price') - F('amount'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).distinct()

        return qs

    def get_urls(self):
        """Add a custom URL to fetch order details dynamically"""
        urls = super().get_urls()
        custom_urls = [
            path('get-order-total/', self.get_order_total, name='get_order_total'),
            path('get-amount-to-pay/', self.ajax_retrieve_amount_to_pay, name='get_amount_to_pay'),
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
    def amount_to_pay(self, obj):
        """Retrieve total order amount from annotated queryset"""
        if hasattr(obj, "order_id"):
            order_id = obj.order_id
            previousPayment = Payment.objects.filter(order_id=order_id, created_at__lt=obj.created_at).aggregate(Sum('amount'))['amount__sum'] or 0
            balance = obj.amount_to_pay - previousPayment
        else:
            order_id = obj.id
            previousPayment = Payment.objects.filter(order_id=obj.id).aggregate(Sum('amount'))['amount__sum'] or 0
            balance = obj.get_total_amount() - previousPayment 
          
        return  balance  if   balance  else 0.00
        
    def ajax_retrieve_amount_to_pay(self,request):
        """AJAX endpoint to fetch the amount to pay for a selected order"""
        order_id = request.GET.get('order_id')
        if not order_id:
            return JsonResponse({'error': 'No order ID provided'}, status=400)

        try:
            order = Order.objects.get(id=order_id)
            total_amount = self.amount_to_pay(order)
            return JsonResponse({'amount_to_pay': self.amount_to_pay(order)})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)

    @admin.display(ordering='amount_to_pay', description="Amount to Pay")
    def get_amount_to_pay(self, obj):
        """Retrieve total order amount from annotated queryset"""
        balance = self.amount_to_pay(obj)
        return common.formatted_amount(  balance ) if   balance  else common.formatted_amount(0.00)

    @admin.display(ordering='balance', description="Balance")
    def get_balance(self, obj):
        """Retrieve balance from annotated queryset"""
        # previousPayment date should be less than the current payment date
        previousPayment = self.amount_to_pay(obj)
        # Ensure both values are Decimal
        previousPayment = Decimal(previousPayment)
        balance = previousPayment - Decimal(obj.amount)
        return common.formatted_amount(balance) if balance else common.formatted_amount(0.00)

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
