from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from .models import Order, OrderDetails
from products.models import Product  
from admin_portal.models import CustomUser as User 
from django.db import models

class OrderDetailsForm(forms.ModelForm):
    """Ensures products appear in the dropdown."""
    class Meta:
        model = OrderDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure products appear in dropdown
        self.fields['product'].queryset = Product.objects.all()

        
          
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
        
        # ✅ Override dropdown choices to display Full Name instead of Username
        self.fields['assigned_to'].queryset = User.objects.all().order_by('last_name', 'first_name')
        self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"

        self.fields['customer'].queryset = User.objects.all().order_by('last_name', 'first_name')
        self.fields['customer'].label_from_instance = lambda obj: f"{obj.last_name}, {obj.first_name}"
class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    form = OrderDetailsForm  # Attach the form with proper queryset
    extra = 1
    readonly_fields = ('total_price',)
    fields = ('product', 'delivery_datetime','quantity', 'status', 'remarks', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_assigned_to_name', 'get_customer_name', 'created_at','get_total_price','get_order_status')
    search_fields = ('assigned_to__first_name', 'assigned_to__last_name', 'customer__first_name', 'customer__last_name')
    list_filter = ('customer', 'assigned_to', 'created_at')
    form = OrderAdminForm # Attach the form with proper queryset
    fieldsets = [
        ('Order Info', {'fields': ('assigned_to', 'customer')}),
        ('Map Location', {'fields': ('map_display',)}),  # Map Display
    ]

    readonly_fields = ('created_at', 'map_display')
    inlines = [OrderDetailsInline]

    def get_total_price(self, obj):
        """Calculates the total price of all OrderDetails related to this order."""
        total_price = obj.order_details.aggregate(total=models.Sum('total_price'))['total'] or 0
        return f"₱{total_price:,.2f}"  # Formats with Peso symbol and two decimal places

    get_total_price.short_description = "Total Price"  # Set the column name in Django Admin
    get_total_price.admin_order_field = 'order_details__status'  # Enable sorting

    def get_assigned_to_name(self, obj):
        """Display assigned user's full name in 'Last, First' format."""
        if obj.assigned_to:
            return f"{obj.assigned_to.last_name}, {obj.assigned_to.first_name}"
        return "No Assigned User"
    
    def get_order_status(self, obj):
        """Determines the overall status of the order based on its OrderDetails."""
        statuses = obj.order_details.values_list('status', flat=True)

        if not statuses:  # If no OrderDetails exist, return "No Order Details"
            return "No Order Details"

        if 0 in statuses:  # If at least one order detail is pending
            return "Pending"
        elif all(status == 1 for status in statuses):  # If all are Delivered
            return "Delivered"
        elif all(status == 2 for status in statuses):  # If all are Cancelled
            return "Cancelled"
        else:
            return "Partially Delivered/Cancelled"

    get_order_status.short_description = "Order Status"
    get_order_status.admin_order_field = 'order_details__status'  # Enable sorting

    def get_customer_name(self, obj):
        """Display customer full name in 'Last, First' format."""
        if obj.customer:
            return f"{obj.customer.last_name}, {obj.customer.first_name}"
        return "No Customer"

    get_assigned_to_name.admin_order_field = 'assigned_to__last_name'
    get_assigned_to_name.short_description = "Assigned To"

    get_customer_name.admin_order_field = 'customer__last_name'
    get_customer_name.short_description = "Customer Name"

    def map_display(self, obj):
        """Displays Google Map based on customer location."""
        if obj.customer and obj.customer.lat and obj.customer.long:
            return mark_safe(f"""
                <script>
                function initMap() {{
                    var lat = {obj.customer.lat};
                    var lng = {obj.customer.long};

                    var myLatlng = {{ lat: lat, lng: lng }};
                    var map = new google.maps.Map(document.getElementById('map'), {{
                        zoom: 12,
                        center: myLatlng
                    }});

                    var marker = new google.maps.Marker({{
                        position: myLatlng,
                        map: map,
                        draggable: true
                    }});

                    google.maps.event.addListener(marker, 'dragend', function(event) {{
                        var newLat = event.latLng.lat();
                        var newLng = event.latLng.lng();
                    }});
                }}
                </script>
                <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAy1hLcI4XMz-UV-JgZJswU5nXcQHcL6mk&callback=initMap" async defer></script>
                <div id="map" style="height: 400px;"></div>
            """)
        return "No location available"

    map_display.short_description = "Customer Location Map"


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'get_products', 'delivery_datetime', 'status', 'total_price')
    list_filter = ('status', 'delivery_datetime')
    search_fields = ('order__id',)
    form = OrderDetailsForm  # Use the form with correct product queryset

    readonly_fields = ('total_price',)

    def get_products(self, obj):
        """Returns the product name."""
        return obj.product.name if obj.product else ""


    get_products.short_description = "Products"
