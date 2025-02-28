from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from .models import Order, OrderDetails
from products.models import Product  
from admin_portal.models import CustomUser as User 
from django.db import models, transaction
from django.http import HttpResponse
import openpyxl
from django.utils.translation import gettext_lazy as _
from settings.models import StoreSettings
from django.forms import NumberInput
import json
class OrderDetailsForm(forms.ModelForm):
    class Meta:
        model = OrderDetails
        fields = '__all__'
        widgets = {
            'quantity': NumberInput(attrs={'step': '1', 'min': '1','class':'field-quantity'})  # Force step of 1
        }
    class Media:
        js = ('admin/js/update_total_price.js',)  # Load the JavaScript file

   
class OrderAdminForm(forms.ModelForm):
    """Customizes the 'assigned_to' and 'customer' dropdowns to show full name."""
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Assigned To",
        widget=forms.Select,
        required=True
    )

    customer = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Customer",
        widget=forms.Select,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assigned_to'].queryset = User.objects.filter(user_type=1).order_by('last_name', 'first_name')
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"

        self.fields['customer'].queryset = User.objects.filter(user_type=0).order_by('last_name', 'first_name')
        self.fields['customer'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"

class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 1
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'total_price')
    form = OrderDetailsForm  # Apply the custom form
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            products = Product.objects.all()
            kwargs["widget"] = forms.Select(attrs={
                "class": "field-product",
                "data-product-prices": json.dumps({p.id: float(p.price) for p in products})  # Inject prices
            })
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_assigned_to_name', 'get_customer_name', 'created_at', 'get_total_price', 'status', 'delivery_datetime')
    search_fields = ('assigned_to__first_name', 'assigned_to__last_name', 'customer__first_name', 'customer__last_name')
    list_filter = ('customer', 'assigned_to', ('created_at', admin.DateFieldListFilter))
    form = OrderAdminForm
    readonly_fields = ('created_at',)
    inlines = [OrderDetailsInline]
    ordering = ('-created_at', 'status', 'delivery_datetime')

    def save_model(self, request, obj, form, change):
        """Ensure stock is deducted when status is changed to Delivered (status=4)"""
        previous_status = None
        if obj.pk:
            previous_status = Order.objects.get(pk=obj.pk).status  # Get previous status before update

        super().save_model(request, obj, form, change)  # Save the model first

        # ✅ Deduct stock if status is changed to Delivered
        if obj.status == 4 and previous_status != 4:  # Only deduct if it was NOT previously delivered
            with transaction.atomic():
                for order_detail in OrderDetails.objects.filter(order=obj):
                    product = order_detail.product
                    if product.stock >= order_detail.quantity:
                        product.stock -= order_detail.quantity
                        product.save()
                    else:
                        self.message_user(request, f"⚠️ Not enough stock for {product.name}. Only {product.quantity} left.", level="error")

    def get_total_price(self, obj):
        """Calculates the total price of all OrderDetails related to this order."""
        store_settings = StoreSettings.objects.first()
        total_price = obj.order_details.aggregate(total=models.Sum('total_price'))['total'] or 0
        return f"{store_settings.currency_symbol}{total_price:,.2f}"

    get_total_price.short_description = "Total Price"
    get_total_price.admin_order_field = 'order_details__status'

    def get_assigned_to_name(self, obj):
        """Display assigned user's full name in 'Last, First' format."""
        return f"{obj.assigned_to.last_name}, {obj.assigned_to.first_name}" if obj.assigned_to else "No Assigned User"

    def get_customer_name(self, obj):
        """Display customer full name in 'Last, First' format."""
        return f"{obj.customer.last_name}, {obj.customer.first_name}" if obj.customer else "No Customer"

    get_assigned_to_name.short_description = "Assigned To"
    get_customer_name.short_description = "Customer Name"

@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'get_products', 'total_price')
    list_filter = ('order', 'total_price')
    search_fields = ('order__id',)
    readonly_fields = ('total_price',)

    def get_products(self, obj):
        """Returns the product name."""
        return obj.product.name if obj.product else ""

    get_products.short_description = "Products"
