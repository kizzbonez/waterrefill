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
    form = CustomUserForm
    # Show these fields in the user list
    list_display = ["username", "email", "first_name", "last_name", "phone_number", "user_type", "is_staff"]
    def google_map(self, obj=None):
        return CustomUserForm.google_map(self)
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


