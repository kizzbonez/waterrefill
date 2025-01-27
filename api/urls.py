from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import HelloWorldView  # Import directly from views.py
from .api_views.users import UserInfoView
from .custom_serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
     path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('hello/', HelloWorldView.as_view(), name='hello_world'),  # Example API
    path('user/', UserInfoView.as_view(), name='hello_world'),  # Example API
]
