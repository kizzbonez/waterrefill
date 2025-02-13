from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .api_views.users import UserInfoView ,RiderClientDetailView,RiderEditClientView ,RiderClientListView, UserRegistrationView ,PasswordResetRequestView, PasswordResetConfirmView
from .api_views.orders import OrderListCreateView, OrderDetailView
from .api_views.products import ProductListView ,ProductDetailView 
from .api_views.logout import LogoutView
from .api_views.payments import ClientPaymentView, RiderPaymentView, RiderPaymentGetView
from .custom_serializers import CustomTokenObtainPairSerializer, RiderTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainPairView
# Define custom login views
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RiderTokenObtainPairView(TokenObtainPairView):
    serializer_class = RiderTokenObtainPairSerializer

urlpatterns = [
    #Authentication process
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('user/', UserInfoView.as_view(), name='user'),  # Example API
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    #access product list
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),

    #orders
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),


    #payment
    path('payments/', ClientPaymentView.as_view(), name='client-payments'),  # Clients: Add & View Payments
    path('rider/payments/', RiderPaymentView.as_view(), name='rider-payments'),  # Riders: View & Create Payments
    path('rider/payments/<int:id>/', RiderPaymentGetView.as_view(), name='rider-get-payments'),  # Riders: View & Create Payments
    #endpoints for rider only
    path('rider/login/', RiderTokenObtainPairView.as_view(), name='rider_token_obtain_pair'),  # Rider login
    path('rider/all-client/', RiderClientListView.as_view(), name='list-clients'),  # Riders edit client details
    path('rider/get-client/<int:user_id>/', RiderClientDetailView.as_view(), name='client-detail'),
    path('rider/edit-client/<int:user_id>/', RiderEditClientView.as_view(), name='edit-client'),  # Riders edit client details


]
