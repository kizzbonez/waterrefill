import openpyxl
import pandas as pd
import numpy as np
from django.http import HttpResponse
from django.contrib import admin
from django.db import models  # Import Django's models module
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import make_password
from django import forms
from django.utils.safestring import mark_safe
from .models import CustomUser, ThemeSettings
from django.template.response import TemplateResponse
from django.urls import path
from .models import CustomUser # Import your models
from orders.models import Order , OrderDetails
from payments.models import Payment
from settings.models import StoreSettings
from django.db.models import Sum, Min
from django.db.models.functions import TruncMonth, TruncDay
import locale
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from products.models import Product  # Import your Product model
from settings.models import StoreSettings  # Import your Product model
locale.setlocale(locale.LC_ALL, 'en_PH.UTF-8')
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
class CustomAdmin(admin.AdminSite):
    """Custom Admin Dashboard with Jazzmin (Without admin_site)"""

    index_template = "admin/index.html"  #  Use custom index template

    def sales_forecast(self,sales_data):
              #this is the code for the forecast of sales
        sales_data_past_months = sales_data[:-1]

        # Number of months in past sales data
        num_months = len(sales_data_past_months)
       
        # Weights from 1 to n (most recent has highest weight)
        weights = np.arange(1,  num_months + 1)
        # Compute Weighted Moving Average (WMA)
        sales_sum= sum(sales_data_past_months)
        wma_value_sales = round(np.dot(sales_data_past_months, weights) / weights.sum(),2)
        return wma_value_sales
   
    def products_forecast(self):
        # Fetch product data
        products = Product.objects.all()
        forecast = []

        for product in products:
            product_id = product.id
            product_name = product.name

            # Query monthly sold quantity
            monthly_sold_data = (
                OrderDetails.objects.filter(product_id=product_id, order__status=4)
                .annotate(month=TruncMonth("order__created_at"))
                .values("month")
                .annotate(total_sold=Sum("quantity"))
                .order_by("month")
            )
            # Convert to lists
            labels = [entry["month"].strftime("%b %Y") for entry in monthly_sold_data]
            monthly_sold = [float(entry["total_sold"]) for entry in monthly_sold_data]
            # Skip products with no sales data
            if not monthly_sold:
                forecast.append({
                    "product_name": product_name,
                    "product_id": product_id,
                    "wma_value_product_sold": 0,
                    "mape_value": 0
                })
                continue

            # Use only the most recent sales data for WMA
            product_sold_past_months = monthly_sold[-3:]  # Take last 3 months (change as needed)

            # Ensure at least one month of data exists
            if not product_sold_past_months:
                forecast.append({
                    "product_name": product_name,
                    "product_id": product_id,
                    "wma_value_product_sold": 0,
                    "mape_value": 0
                })
                continue

            num_months = len(product_sold_past_months)
            weights = np.arange(1, num_months + 1)

            # Compute Weighted Moving Average (WMA)
            wma_value_product_sold = round(
                np.dot(product_sold_past_months, weights) / weights.sum(), 2
            )

            # Compute MAPE (Mean Absolute Percentage Error)
            if len(monthly_sold) >= 2:
                last_actual_value = monthly_sold[-1]
                if last_actual_value != 0:  # Avoid division by zero
                    mape_value = abs((last_actual_value - wma_value_product_sold) / last_actual_value) * 100
                else:
                    mape_value = 0
            else:
                mape_value = 0  # Not enough data for MAPE calculation

            forecast.append({
                "product_name": product_name,
                "product_id": product_id,
                "wma_value_product_sold": wma_value_product_sold,
                "mape_value": mape_value
            })

        return forecast


    def index(self, request, extra_context=None):
        """Inject dashboard data into the default Django Admin"""
        if extra_context is None:
            extra_context = {}
        


         #  Aggregate total revenue per month
        monthly_sales = (
            Payment.objects.filter(status=1)  #  Filter only completed payments
            .annotate(month=TruncMonth("created_at"))  #  Group by month
            .values("month")
            .annotate(total=Sum("amount"))  #  Sum payments per month
            .order_by("month")  #  Order by month
        )

        first_payment = Payment.objects.filter(status=1).aggregate(earliest=Min("created_at"))["earliest"]
        start_date = first_payment if first_payment else timezone.now() - timedelta(days=30)

        today = timezone.now()
        #last_30_days = today - timezone.timedelta(days=30)
       # start_date = today - timedelta(days=30)

        # ✅ Fetch sales data (only existing sales days)
        sales_query = Payment.objects.filter(status=1, created_at__range=[start_date, today]) \
            .annotate(day=TruncDay("created_at")) \
            .values("day") \
            .annotate(total=Sum("amount")) \
            .order_by("day")

        # ✅ Convert to dictionary for fast lookup
        sales_dict = {entry["day"].date(): float(entry["total"]) for entry in sales_query}

        # ✅ Generate full date range from `start_date` to `today`
        all_dates = pd.date_range(start=start_date.date(), end=today.date(), freq="D")

        # ✅ Fill in missing days with 0 sales
        filled_sales = [{"day": date, "total": sales_dict.get(date.date(), 0)} for date in all_dates]

        # ✅ Extract labels & data for charts
        daily_sales_labels = [entry["day"].strftime("%b %d") for entry in filled_sales]
        daily_sales_data = [entry["total"] for entry in filled_sales]

        #  Extract labels (months) and data (total revenue per month)
        sales_labels = [entry["month"].strftime("%b %Y") for entry in monthly_sales]  # Example: ['Jan 2024', 'Feb 2024']
        sales_data = [float(entry["total"]) for entry in monthly_sales]  # Convert to float for Chart.js

        wma_value_sales = self.sales_forecast(sales_data)
        # Calculate the Mape (total sales - wma) / total sales * 100
        mape_value = ((sales_data[-1] - wma_value_sales) / sales_data[-1] ) * 100

        product_forecasts = self.products_forecast()
       

        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month_start = (current_month_start + timezone.timedelta(days=32)).replace(day=1)

        total_revenue = Payment.objects.filter(
            status=1,  #  Only completed payments
            created_at__gte=current_month_start,  #  Start of current month
            created_at__lt=next_month_start  #  Start of next month
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        critical_products = Product.objects.filter(stock__lte=models.F('stock_alert_level'))

        # Format for display
        formatted_critical_products = [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock,
                "alert_level": product.stock_alert_level,
                "status": "Critical" if product.stock == 0 else "Low Stock"
            }
            for product in critical_products
            if product.stock_alert_level not in [None, 0]
        ]
        # pass active products to the template
        formatted_products = [
            {
                "id": product.id,
                "name": product.name,
                "stock": product.stock,
            }
            for product in Product.objects.filter(status=1)
        ]
        extra_context["critical_products"] = formatted_critical_products
        extra_context["product_forecasts"] = []
        extra_context["total_revenue"] = locale.currency(total_revenue, grouping=True)
        extra_context["total_users"] = CustomUser.objects.count()
        extra_context["total_orders"] = Order.objects.count()
        extra_context["pending_orders"] = Order.objects.filter(status=0).count()
        extra_context["sales_labels"] =  sales_labels
        extra_context["product_forecasts"] = product_forecasts
        extra_context["all_products"] =    formatted_products
        extra_context["sales_data"] =   sales_data # Example sales data
        extra_context["current_month"] = datetime.now().strftime("%B") 
        extra_context["forecast_sales"] =    locale.currency(wma_value_sales, grouping=True)  # Example sales data
        extra_context["mape_sales"] =  f"{mape_value:.2f}%"  # Example MAPE value
        extra_context["products"] = Product.objects.all()
            #  Fetch order data with user and total amount
        recent_orders = Order.objects.select_related('customer').prefetch_related('order_details').order_by('-created_at')[:5]

        formatted_orders = []
        store_settings = StoreSettings.objects.first()
        for order in recent_orders:
            total_amount = order.get_total_amount()  #  Calculate total amount
            formatted_orders.append({
                "order_id": order.id,
                "customer_name": order.customer.get_full_name() or order.customer.username,  #  Display full name or username
                "total_amount": f"{store_settings.currency_symbol}{total_amount:,.2f}",  #  Format as PHP currency
                "status": order.get_status_display(),  #  Convert status integer to text
            })

        #  Pass formatted orders to the template
        extra_context["recent_orders"] = formatted_orders
        
        return super().index(request, extra_context=extra_context)

#  Attach this to Django's default admin
admin.site.__class__ = CustomAdmin
 
class CustomUserForm(forms.ModelForm):
    """Custom form for the User model, allowing the admin to change the password."""
    
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        required=False,  # Admins can leave it blank if they don't want to change the password
    )


    class Meta:
        model = CustomUser
        fields = "__all__"

    def save(self, commit=True):
        """Overrides the save method to hash and store a new password if provided."""
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
       
        if new_password:  # If admin entered a new password, hash it before saving
            user.password = make_password(new_password)

        if commit:
            user.save()
        return user

    def google_map(self):
        store_latitude = StoreSettings.objects.first().store_latitude
        store_longitude = StoreSettings.objects.first().store_longitude
        settings = StoreSettings.objects.first()
        return mark_safe(f"""
            <script>
                function initMap() {{
                    var latInput = document.getElementById("id_lat");
                    var lngInput = document.getElementById("id_long");
                    var distanceText = document.getElementById("distance_km"); // ✅ Distance display

                    // ✅ Default user location (Manila)
                    var defaultLat = parseFloat(latInput.value) || 14.5995;
                    var defaultLng = parseFloat(lngInput.value) || 120.9842;
                    var userLocation = {{ lat: defaultLat, lng: defaultLng }};

                    // ✅ Fixed Start Location 
                    var startPoint = {{ lat: {store_latitude}, lng: {store_longitude} }};

                    var map = new google.maps.Map(document.getElementById('map'), {{
                        zoom: 12,
                        center: userLocation
                    }});

                    var marker = new google.maps.Marker({{
                        position: userLocation,
                        map: map,
                        draggable: true
                    }});

                    var service = new google.maps.DistanceMatrixService();
                    var directionsService = new google.maps.DirectionsService();
                    var directionsRenderer = new google.maps.DirectionsRenderer({{
                        map: map
                    }});

                    function calculateRoute(destination) {{
                        directionsService.route(
                            {{
                                origin: startPoint,
                                destination: destination,
                                travelMode: 'DRIVING',
                            }},
                            function(response, status) {{
                                if (status === 'OK') {{
                                    directionsRenderer.setDirections(response);
                                    var distance = response.routes[0].legs[0].distance.text;
                                    distanceText.innerHTML = `🚗 Driving Distance: `+distance;
                                }} else {{
                                    distanceText.innerHTML = "🚗 Route Not Available";
                                }}
                            }}
                        );
                    }}

                    // ✅ Calculate initial route
                    calculateRoute(userLocation);

                    google.maps.event.addListener(marker, 'dragend', function(event) {{
                        var newLat = event.latLng.lat();
                        var newLng = event.latLng.lng();
                        latInput.value = newLat;
                        lngInput.value = newLng;

                        var newLocation = {{ lat: newLat, lng: newLng }};
                        calculateRoute(newLocation);
                    }});
                }}
            </script>

            <script src="https://maps.googleapis.com/maps/api/js?key={settings.gmap_api_key}&callback=initMap" async defer></script>

            <!-- ✅ Display Distance -->
            <div id="distance_km" style="margin-top: 10px; font-weight: bold;"></div>

            <!-- ✅ Google Map Container -->
            <div id="map" style="height: 400px;"></div>
        """)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lat"].widget.attrs["readonly"] = False
        self.fields["long"].widget.attrs["readonly"] = False


class CustomUserAdmin(UserAdmin):
    """Admin settings for managing CustomUser."""
    
    model = CustomUser
    form = CustomUserForm  # Use the updated form
    
    list_display = ("username","fullname", "email", "user_type", "is_active", "is_staff","date_joined")
    list_filter = ("user_type", "is_active", "is_staff", "date_joined")
    ordering = ('date_joined', 'username', 'email', 'is_active','is_staff',"first_name", "last_name") 
    actions = ["export_to_excel"]  #  Add the export action

    def fullname(self, obj):
        return f"{obj.last_name}, {obj.first_name}"

    fullname.short_description = "Full Name"  # Custom column title
    fullname.admin_order_field = "first_name"  # Enables sorting
    # Allow Admins to export user data
    def export_to_excel(self, request, queryset):
        """Exports selected users to an Excel file."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users Data"

        headers = ["Username", "Email", "First Name", "Last Name", "Phone Number", 
                   "User Type", "Address", "Latitude", "Longitude", "Is Staff", 
                   "Is Active", "Last Login", "Date Joined"]
        ws.append(headers)  # Add headers

        for user in queryset:
            ws.append([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.phone_number,
                user.user_type,
                user.address,
                user.lat,
                user.long,
                user.is_staff,
                user.is_active,
                user.last_login.replace(tzinfo=None) if user.last_login else None,
                user.date_joined.replace(tzinfo=None) if user.date_joined else None
            ])

        response = HttpResponse(content_type="application/vnd.openpyxl")
        response["Content-Disposition"] = 'attachment; filename="users_export.xlsx"'
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected users to Excel"

    # Google Map
    def google_map(self, obj=None):
        return CustomUserForm.google_map(self)

    # Permissions
    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.user_type == 2

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2

    # Add new fields to "Personal Info"
    fieldsets = (
        ("Account Info", {"fields": ("user_type","username",'new_password')}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Map", {"fields": ("lat", "long", "google_map")}),
    )
    readonly_fields = ["google_map"]
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {"fields": ("username", "email", "password1", "password2")}),
    )
    # Ensure new fields appear in the "Add User" form
    # add_fieldsets = (
    #     ("Account Info", {"fields": ("user_type","username" )}),
    #     ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),
    #     ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    #     ("Map", {"fields": ("lat", "long")}),
    # )

admin.site.register(CustomUser, CustomUserAdmin)  # Ensure it's registered
