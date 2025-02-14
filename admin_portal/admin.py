import openpyxl
import pandas as pd
import numpy as np
from django.utils import timezone
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
locale.setlocale(locale.LC_ALL, 'en_PH.UTF-8')
class CustomAdmin(admin.AdminSite):
    """Custom Admin Dashboard with Jazzmin (Without admin_site)"""

    index_template = "admin/index.html"  #  Use custom index template

    
    def calculate_wma(self, sales_data, growth_rate=0.0, forecast_days=6):
        """
        Calculate the Weighted Moving Average (WMA) for the given sales data
        and forecast future sales with an optional growth rate.
        
        :param sales_data: List of historical sales
        :param growth_rate: Daily growth rate for forecasting future sales (default is 0% growth)
        :param forecast_days: Number of days to forecast (default is 6)
        :return: List of forecasted sales for future dates
        """

        # Convert sales data to a DataFrame for easier manipulation
        df = pd.DataFrame({'sales': sales_data})

        # 1. Replace zeros with NaN (so we can fill them with meaningful values)
        df['sales'] = df['sales'].replace(0, np.nan)

        # 2. Apply smoothing - Choose one:
        df['sales'] = df['sales'].interpolate(method='linear')  # Linear Interpolation
        # df['sales'] = df['sales'].fillna(df['sales'].rolling(3, min_periods=1).mean())  # Rolling Mean
        # df['sales'] = df['sales'].fillna(df['sales'].ewm(span=3, adjust=False).mean())  # Exponential Smoothing

        # If any zeros are still present (e.g., at the start), replace them with a small value
        df['sales'] = df['sales'].fillna(method='bfill')  # Fill remaining NaN with the next available value

        # Convert back to list after smoothing
        smoothed_sales = df['sales'].tolist()

        # Define weights (e.g., more recent sales data has higher weight)
        weights = list(range(1, len(smoothed_sales) + 1))  # weights from 1 to n
        total_weight = sum(weights)

        # Calculate WMA for the last available day
        wma = sum([s * w for s, w in zip(smoothed_sales, weights)]) / total_weight

        # Print WMA for the last day (just for clarity)
        print(f"Weighted Moving Average for the last available day: {wma}")

        # Forecast sales for the next `forecast_days` using the WMA and growth rate
        forecast_sales = []
        for i in range(forecast_days):  # Forecasting `forecast_days` days
            forecasted_value = wma * (1 + growth_rate)**i  # Adjust for growth rate
            forecast_sales.append(forecasted_value)

        return forecast_sales


    def calculate_mape(self, actual_sales, forecast_sales):
        """
        Compute the Mean Absolute Percentage Error (MAPE) between actual and forecasted sales.
        
        :param actual_sales: List of actual sales values for the forecast period
        :param forecast_sales: List of forecasted sales values for the same period
        :return: MAPE percentage
        """
        errors = []
        for actual, forecast in zip(actual_sales, forecast_sales):
            if actual == 0:
                continue  # Skip if actual sales are zero
            abs_percentage_error = abs((actual - forecast) / actual) * 100
            errors.append(abs_percentage_error)

        # Calculate and return the average MAPE
        return sum(errors) / len(errors) if errors else 0


    def index(self, request, extra_context=None):
        """Inject dashboard data into the default Django Admin"""
        if extra_context is None:
            extra_context = {}
        

        # Get start and end date from request
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        # Define the expected date format
        date_format = "%Y-%m-%d"

        try:
            # Convert string dates to datetime (if provided)
            start_date_fi = datetime.strptime(start_date_str, date_format) if start_date_str else None
            end_date_fi = datetime.strptime(end_date_str, date_format) if end_date_str else None
        except ValueError:
            # Handle invalid date formats
            start_date_fi = None
            end_date_fi = None

        # ✅ If no valid start date, use the first entry from the database
        if start_date_fi is None:
            first_payment = Payment.objects.filter(status=1).aggregate(earliest=Min("created_at"))["earliest"]
            start_date_fi = first_payment if first_payment else timezone.now() - timedelta(days=30)

        # ✅ If no valid end date, use today's date
        if end_date_fi is None:
            end_date_fi = timezone.now()

        # ✅ Ensure start_date_fi is before end_date_fi
        if start_date_fi > end_date_fi:
            start_date_fi, end_date_fi = end_date_fi, start_date_fi  # Swap if reversed

        # Calculate the number of days in the range
        date_diff = end_date_fi  - start_date_fi 
        num_days = date_diff.days  # This will give you the number of days between the two dates
        #  Fetch analytics data

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
        # Calculate Weighted Moving Average (WMA)
        wma_value = self.calculate_wma(   daily_sales_data, 0,num_days)

         # ✅ Calculate MAPE (Mean Absolute Percentage Error)
        mape_value = self.calculate_mape(   daily_sales_data, wma_value)
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
        ]

        # Pass to the template
        extra_context["critical_products"] = formatted_critical_products

        extra_context["total_revenue"] = locale.currency(total_revenue, grouping=True)
        extra_context["total_users"] = CustomUser.objects.count()
        extra_context["total_orders"] = Order.objects.count()
        extra_context["pending_orders"] = Order.objects.filter(status=0).count()
        extra_context["sales_labels"] =  sales_labels
        extra_context["sales_data"] =   sales_data # Example sales data
        extra_context["forecast"] =    locale.currency(sum(wma_value), grouping=True)  # Example sales data
        extra_context["mape"] =  f"{mape_value:.2f}%"  # Example MAPE value
        extra_context["start_date"] =  start_date_str
        extra_context["end_date"] =  end_date_str
            #  Fetch order data with user and total amount
        recent_orders = Order.objects.select_related('customer').prefetch_related('order_details').order_by('-created_at')[:5]

        formatted_orders = []
        for order in recent_orders:
            total_amount = order.get_total_amount()  #  Calculate total amount
            formatted_orders.append({
                "order_id": order.id,
                "customer_name": order.customer.get_full_name() or order.customer.username,  #  Display full name or username
                "total_amount": f"₱{total_amount:,.2f}",  #  Format as PHP currency
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
        print(  store_latitude  )
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

            <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAy1hLcI4XMz-UV-JgZJswU5nXcQHcL6mk&callback=initMap" async defer></script>

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
    
    list_display = ("username", "email", "user_type", "is_active", "is_staff","date_joined")
    list_filter = ("user_type", "is_active", "is_staff", "date_joined")
    actions = ["export_to_excel"]  #  Add the export action

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
        ("Account Info", {"fields": ("user_type","username", "new_password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Map", {"fields": ("lat", "long", "google_map")}),
    )
    readonly_fields = ["google_map"]

    # Ensure new fields appear in the "Add User" form
    add_fieldsets = (
        ("Account Info", {"fields": ("user_type","username" ,"new_password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Map", {"fields": ("lat", "long")}),
    )

admin.site.register(CustomUser, CustomUserAdmin)  # Ensure it's registered
