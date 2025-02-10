import openpyxl
import pandas as pd
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import admin
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
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDay
import locale
from datetime import datetime
locale.setlocale(locale.LC_ALL, 'en_PH.UTF-8')
class CustomAdmin(admin.AdminSite):
    """Custom Admin Dashboard with Jazzmin (Without admin_site)"""

    index_template = "admin/index.html"  #  Use custom index template

    

    def calculate_wma(self, sales_data, period=3):
        """
        ✅ Compute Weighted Moving Average (WMA) on Daily Sales
        :param sales_data: List of revenue values per day
        :param period: Number of days to consider in WMA (default=3)
        :return: List of WMA values for each period
        """
        wma_values = []
        weights = list(range(1, period + 1))  # e.g., [1, 2, 3] for 3-day WMA
        weight_sum = sum(weights)  # Sum of weights (e.g., 1+2+3 = 6)

        for i in range(len(sales_data)):
            if i < period - 1:
                wma_values.append(None)  # Not enough data points for WMA
                continue

            weighted_sum = sum(sales_data[i - j] * weights[j] for j in range(period))
            wma_values.append(round(weighted_sum / weight_sum, 2))  # ✅ Rounded WMA


        return wma_values
    def calculate_mape(self, actual_sales, forecast_sales):
        """
        ✅ Compute Mean Absolute Percentage Error (MAPE) on Daily Sales
        :param actual_sales: List of actual revenue per day
        :param forecast_sales: List of daily WMA (forecasted) values
        :return: MAPE percentage
        """
        errors = []
        for i in range(len(actual_sales)):
            if forecast_sales[i] is None or actual_sales[i] == 0:
                continue  # ✅ Skip if there's not enough data or actual sales are zero

            abs_percentage_error = abs((actual_sales[i] - forecast_sales[i]) / actual_sales[i]) * 100
            errors.append(abs_percentage_error)

        return round(sum(errors) / len(errors), 2) if errors else 0  # ✅ Return rounded MAPE value


    def index(self, request, extra_context=None):
        """Inject dashboard data into the default Django Admin"""
        if extra_context is None:
            extra_context = {}
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                start_date = timezone.now() - timezone.timedelta(days=30)
                end_date = timezone.now()
        else:
            start_date = timezone.now() - timezone.timedelta(days=30)
            end_date = timezone.now()
        #  Fetch analytics data

         #  Aggregate total revenue per month
        monthly_sales = (
            Payment.objects.filter(status=1)  #  Filter only completed payments
            .annotate(month=TruncMonth("created_at"))  #  Group by month
            .values("month")
            .annotate(total=Sum("amount"))  #  Sum payments per month
            .order_by("month")  #  Order by month
        )


        today = timezone.now()
        last_30_days = today - timezone.timedelta(days=30)

        daily_sales = (
            Payment.objects.filter(status=1, created_at__range=[start_date, end_date])  # ✅ Only last 30 days
            .annotate(day=TruncDay("created_at"))  # ✅ Group by day
            .values("day")
            .annotate(total=Sum("amount"))  # ✅ Sum payments per day
            .order_by("day")
        )


        # ✅ Extract labels and revenue data for daily sales
        daily_sales_labels = [entry["day"].strftime("%b %d") for entry in daily_sales]  # ['Feb 01', 'Feb 02']
        daily_sales_data = [float(entry["total"]) for entry in daily_sales]





        #  Extract labels (months) and data (total revenue per month)
        sales_labels = [entry["month"].strftime("%b %Y") for entry in monthly_sales]  # Example: ['Jan 2024', 'Feb 2024']
        sales_data = [float(entry["total"]) for entry in monthly_sales]  # Convert to float for Chart.js
        # Calculate Weighted Moving Average (WMA)
        wma_values = self.calculate_wma(   daily_sales_data)
        print(      daily_sales_data)
         # ✅ Calculate MAPE (Mean Absolute Percentage Error)
        mape_value = self.calculate_mape(   daily_sales_data, wma_values)
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month_start = (current_month_start + timezone.timedelta(days=32)).replace(day=1)

        total_revenue = Payment.objects.filter(
            status=1,  #  Only completed payments
            created_at__gte=current_month_start,  #  Start of current month
            created_at__lt=next_month_start  #  Start of next month
        ).aggregate(Sum("amount"))["amount__sum"] or 0

        extra_context["total_revenue"] = locale.currency(total_revenue, grouping=True)
        extra_context["total_users"] = CustomUser.objects.count()
        extra_context["total_orders"] = Order.objects.count()
        extra_context["pending_orders"] = Order.objects.filter(status=0).count()
        extra_context["sales_labels"] =  sales_labels
        extra_context["sales_data"] =   sales_data # Example sales data
        extra_context["forecast"] =   mape_value # Example sales data
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
    
    list_display = ("username", "email", "user_type", "is_active", "is_staff")
    ordering = ('id',)  # Optional: Controls sorting
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
