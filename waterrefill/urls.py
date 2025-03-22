from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from admin_portal.views import CustomLoginView
from django.shortcuts import redirect
urlpatterns = [
    path('accounts/login/', lambda request: redirect('/admin/login/')),
    path('accounts/profile/', lambda request: redirect('/admin/login/')),
    path('api/v1/', include('api.urls')),  # Include API URLs
    path('admin/', admin.site.urls),
    path('admin-api/', include('admin_portal.urls')),  # ✅ Register the Admin AP
    path("accounts/", include("django.contrib.auth.urls")),  # 
    path("", include("reports.urls")),
]

# Enable media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
