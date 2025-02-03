import openpyxl
import pandas as pd
from django.http import HttpResponse
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import ThemeSettings
from django import forms
from django.utils.safestring import mark_safe
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = "__all__"

    def google_map(self):
        return mark_safe(f"""
             <script>
         function initMap() {{
                var latInput = document.getElementById("id_lat");
                var lngInput = document.getElementById("id_long");

                var lat = parseFloat(latInput.value) || 14.5995; // Default Manila
                var lng = parseFloat(lngInput.value) || 120.9842;
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
                    latInput.value = newLat;  // ✅ Updates lat field
                    lngInput.value = newLng;  // ✅ Updates long field
                }});
            }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAy1hLcI4XMz-UV-JgZJswU5nXcQHcL6mk&callback=initMap" async defer></script>
            <div id="map" style="height: 400px;">test</div>
          
           
            """)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lat"].widget.attrs["readonly"] = False
        self.fields["long"].widget.attrs["readonly"] = False



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', "phone_number",'address','long','lat', 'is_staff', 'is_active']
    ordering = ('id',)  # Optional: Controls sorting
    actions = ["export_to_excel"]  # ✅ Add the export action
    form = CustomUserForm
    # Show these fields in the user list
    list_display = ["username", "email", "first_name", "last_name", "phone_number", "user_type", "is_staff"]


    def export_to_excel(self, request, queryset):
        """Exports selected users to an Excel file."""
        # Create an Excel workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users Data"

        # Define headers
        headers = ["Username",
         "Email",
         "First Name",
         "Last Name", 
         "Phone Number", 
         "User Type", 
         "Address", 
         "Latitude", 
         "Longitude", 
         "Is Staff", 
         "Is Active", 
         "Last Login", 
         "Date Joined"]
        ws.append(headers)  # Add headers to the worksheet

        # Add user data
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
                user.last_login.replace(tzinfo=None) if user.last_login else None,  # Remove timezone
                user.date_joined.replace(tzinfo=None) if user.date_joined else None  # Remove timezone
            ])

        # Create response object with appropriate headers
        response = HttpResponse(
            content_type="application/vnd.openpyxl",
        )
        response["Content-Disposition"] = 'attachment; filename="users_export.xlsx"'

        # Save the workbook to the response
        wb.save(response)
        return response

    export_to_excel.short_description = "Export selected users to Excel"  # Name for the admin action

    # Google Map
    def google_map(self, obj=None):
        return CustomUserForm.google_map(self)

    #Allow only authenticated Admin users (user_type=2) to access Django Admin.
    def has_module_permission(self, request):

        if not request.user.is_authenticated: 
            return False
        if request.user.is_superuser:  
            return True
        return request.user.user_type == 2  

    #Block non-admin users from viewing objects.
    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2


    #Prevent non-admin users from adding objects.
    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2
        
    #Prevent non-admin users from changing objects.
    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2

    #Prevent non-admin users from deleting objects.
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.user_type == 2   



    # Add new fields to "Personal Info"
    fieldsets = (
        ("General", {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address")}),  # Modified
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Other Info", {"fields": ("user_type",)}),
        ("Map", {
            "fields": ("lat", "long","google_map"),
        }),
    )
    readonly_fields = ["google_map"]
    # Ensure new fields appear in the "Add User" form
    add_fieldsets = (
        ("General", {"fields": ("username", "password1", "password2")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "address",)}),  # Modified
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Other Info", {"fields": ("user_type",)}),
    ) 
admin.site.register(CustomUser, CustomUserAdmin)  # Ensure it's registered


