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
import openpyxl
from django.http import HttpResponse
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from payments.models import Payment
from django.contrib.admin import SimpleListFilter
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.utils import timezone
class OrderDetailsForm(forms.ModelForm):
    class Meta:
        model = OrderDetails
        fields = '__all__'
        widgets = {
            'quantity': NumberInput(attrs={'step': '1', 'min': '1','class':'field-quantity'})  # Force step of 1
        }
    class Media:
        js = ('admin/js/update_total_price_updated_1.js',)  # Load the JavaScript file

   
class OrderAdminForm(forms.ModelForm):
    """Customizes the 'assigned_to', 'customer', and 'delivery_datetime' fields."""

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type=1).order_by('last_name', 'first_name'),
        label="Assigned To",
        widget=forms.Select,
        required=True
    )

    customer = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type=0).order_by('last_name', 'first_name'),
        label="Customer",
        widget=forms.Select,
        required=True
    )
    
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            'delivery_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'min': timezone.now().strftime('%Y-%m-%dT%H:%M'),  # prevent past times
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"
        self.fields['customer'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"
        if 'status' in self.fields:
            self.fields['status'].choices = [
                choice for choice in self.fields['status'].choices if choice[0] != 4
            ]

class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 1
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'total_price','current_product_price')
    form = OrderDetailsForm  # Apply the custom form
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            products = Product.objects.all()
            kwargs["widget"] = forms.Select(attrs={
                "class": "field-product",
                "data-product-prices": json.dumps({p.id: float(p.price) for p in products})  # Inject prices
            })     
 
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    class Media:
        css = {
            "all": ("admin/css/custom.css",)  # Add custom CSS file
        }
class CustomerFilter(SimpleListFilter):
    title = _('Customer')
    parameter_name = 'customer'

    def lookups(self, request, model_admin):
        customers = User.objects.filter(user_type=0)
        return [(customer.id, customer.get_full_name() or customer.last_name) for customer in customers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(customer__id=self.value())
        return queryset

# Custom filter for Assigned Users (user_type = 2)
class AssignedToFilter(SimpleListFilter):
    title = _('Assigned To')
    parameter_name = 'assigned_to'

    def lookups(self, request, model_admin):
        assigned_users = User.objects.filter(user_type=1)
        return [(user.id, user.get_full_name() or user.last_name) for user in assigned_users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assigned_to__id=self.value())
        return queryset
class AssignRiderForm(forms.Form):
    rider = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type=1),
        label="Select Rider",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rider'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_assigned_to_name', 'get_customer_name','get_customer_address', 'created_at', 'get_total_price', 'status', 'delivery_datetime')
    search_fields = ('assigned_to__first_name', 'assigned_to__last_name', 'customer__first_name', 'customer__last_name')
    list_filter = (
        ('created_at', DateRangeFilter),  # Date range filter
        CustomerFilter,  # Custom filter for Customers
        'status',  # Regular status filter
        AssignedToFilter,  # Custom filter for Assigned Users
    )
    form = OrderAdminForm
    readonly_fields = ('created_at',)
    inlines = [OrderDetailsInline]
    ordering = ('-created_at', 'status', 'delivery_datetime')
    actions = ["export_to_excel","assign_rider_action"]
    class Media:
        js = ('admin/js/order_admin.js',)  # Load the JavaScript file
    def assign_rider_action(self, request, queryset):
        if "apply" in request.POST:
            form = AssignRiderForm(request.POST)
            if form.is_valid():
                rider = form.cleaned_data["rider"]
                count = queryset.update(assigned_to=rider)
                self.message_user(request, f"✅ Successfully assigned {rider.get_full_name()} to {count} orders.")
                return redirect(request.get_full_path())  # Go back to changelist
        else:
            form = AssignRiderForm()

        return render(request, "admin/assign_rider_form.html", {
            "form": form,
            "queryset": queryset,
            "action": "assign_rider_action",
            "title": "Assign Rider to Selected Orders",
        })

    assign_rider_action.short_description = "Assign selected Orders to a Rider"

    def has_delete_permission(self, request, obj=None):
        """Disables delete option for all products"""
        if obj is None:
         return False  # Prevent deletion if no specific object is provided
        order_id = obj.id
        # Check if the product is in any order
        if Payment.objects.filter(order_id=order_id).exists() or obj.status == 4  or obj.status == 8 :
            return False
        return True
    def has_change_permission(self, request, obj=None):
        """Disables update option for all products"""
        if obj is None:
         return False  # Prevent changes if no specific object is provided
        order_id = obj.id
        # Check if the product is in any order
        if (obj.status == 4  or obj.status == 8):
            return False
        return True
    def export_to_excel(self, request, queryset):
        """Exports selected orders to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Orders Data"

        # ✅ Update headers to match Order model fields
        headers = ["Order ID", "Assigned To", "Customer","Address", "Created At", "Total Price", "Status", "Delivery Datetime"]
        ws.append(headers)

        for order in queryset:
            ws.append([
                order.id,
                order.assigned_to.get_full_name() if order.assigned_to else "N/A",
                order.customer.get_full_name() if order.customer else "N/A",
                order.customer.address if order.customer.address else "N/A",
                order.created_at.strftime("%Y-%m-%d %H:%M:%S"),  # Format date properly
                order.get_total_amount(),  # Calls method to get total price
                order.get_status_display(),  # Convert status integer to text
                order.delivery_datetime.strftime("%Y-%m-%d %H:%M:%S") if order.delivery_datetime else "N/A"
            ])

        # ✅ Set response headers for Excel download
        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="orders_export.xlsx"'
        wb.save(response)
        return response

    # ✅ Short description for action in Django Admin
    export_to_excel.short_description = "Export selected Orders to Excel"


    def save_model(self, request, obj, form, change):
        """Ensure stock is deducted when status is changed to Delivered (status=4)"""
        previous_status = None
        if obj.pk:
            previous_status = Order.objects.get(pk=obj.pk).status  # Get previous status before update

        super().save_model(request, obj, form, change)  # Save the model first

        # ✅ Deduct stock if status is changed to Delivered
        if (obj.status == 4 and previous_status != 4) or (obj.status == 8 and previous_status != 8):  # Only deduct if it was NOT previously delivered
            with transaction.atomic():
                for order_detail in OrderDetails.objects.filter(order=obj):
                    product = order_detail.product
                    if product.water_product:
                        continue  # Skip water products
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
        #filter assigned_to only the rider with user_type=1

        return f"{obj.assigned_to.last_name}, {obj.assigned_to.first_name}" if obj.assigned_to else "No Assigned User"

    def get_customer_name(self, obj):
        """Display customer full name in 'Last, First' format."""

        return f"{obj.customer.last_name}, {obj.customer.first_name}" if obj.customer else "No Customer"
    def get_customer_address(self, obj):
        """Display customer full name in 'Last, First' format."""

        return f"{obj.customer.address}" if obj.customer else "No Address"

    get_assigned_to_name.short_description = "Assigned To"
    get_customer_name.short_description = "Customer Name"
    get_customer_address.short_description = "Customer Address"
class OrderCreatedAtSimpleFilter(admin.SimpleListFilter):
    title = _('Order Date')
    parameter_name = 'order_created_at_range'

    def lookups(self, request, model_admin):
        return [
            ('today', _('Today')),
            ('past_7_days', _('Past 7 days')),
            ('this_month', _('This month')),
            ('this_year', _('This year')),
        ]

    def queryset(self, request, queryset):
        today = datetime.today().date()
        if self.value() == 'today':
            return queryset.filter(order__created_at__date=today)
        elif self.value() == 'past_7_days':
            return queryset.filter(order__created_at__date__gte=today - timedelta(days=7))
        elif self.value() == 'this_month':
            return queryset.filter(order__created_at__month=today.month, order__created_at__year=today.year)
        elif self.value() == 'this_year':
            return queryset.filter(order__created_at__year=today.year)
        return queryset
@admin.register(OrderDetails)

class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'get_products','quantity', 'total_price', 'get_order_created_at')
    list_filter = (
        OrderCreatedAtSimpleFilter,  # ✅ Add date range filter
        'order', 
        'total_price', 
        'product'
    )
    search_fields = ('order__id',)
    readonly_fields = ('total_price',)
    actions = ["export_to_excel"]  # ✅ Add Export action

    def get_products(self, obj):
        """Returns the product name."""
        return obj.product.name if obj.product else ""

    get_products.short_description = "Products"

    def get_order_created_at(self, obj):
        """Returns the created_at timestamp from the related Order model."""
        return obj.order.created_at if obj.order else None

    get_order_created_at.short_description = "Order Created At"
    get_order_created_at.admin_order_field = 'order__created_at'  # Enables sorting

    def export_to_excel(self, request, queryset):
        """Exports selected order details to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Order Details Data"

        # ✅ Define correct headers for Order Details
        headers = ["Order Detail ID", "Order ID", "Product", "Quantity", "Total Price", "Order Created At"]
        ws.append(headers)

        for order_detail in queryset:
            ws.append([
                order_detail.id,
                order_detail.order.id if order_detail.order else "N/A",
                order_detail.product.name if order_detail.product else "N/A",
                order_detail.quantity,
                order_detail.total_price,
                order_detail.order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order_detail.order else "N/A"
            ])

        # ✅ Set response headers for Excel download
        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="order_details_export.xlsx"'
        wb.save(response)
        return response

    # ✅ Short description for the admin action
    export_to_excel.short_description = "Export selected Order Details to Excel"
