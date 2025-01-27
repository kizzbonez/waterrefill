from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('api.urls')),  # Include API URLs
    path('admin/', admin.site.urls),
]
