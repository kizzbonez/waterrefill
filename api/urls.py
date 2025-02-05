from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .api_views.users import UserInfoView ,RiderEditClientView ,RiderClientListView
from .api_views.orders import OrderListCreateView, OrderDetailView
from .api_views.products import ProductListView
from .api_views.logout import LogoutView
from .api_views.payments import ClientPaymentView, RiderPaymentView
from .custom_serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    #Authentication process
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('user/', UserInfoView.as_view(), name='user'),  # Example API
    path('logout/', LogoutView.as_view(), name='logout'),

    #access product list
    path('products/', ProductListView.as_view(), name='product_list'),


    #orders
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),


    #payment
    path('payments/', ClientPaymentView.as_view(), name='client-payments'),  # Clients: Add & View Payments
    path('rider/payments/', RiderPaymentView.as_view(), name='rider-payments'),  # Riders: View & Create Payments

    #endpoints for rider only
    path('rider/all-client/', RiderClientListView.as_view(), name='list-clients'),  # Riders edit client details
    path('rider/edit-client/<int:user_id>/', RiderEditClientView.as_view(), name='edit-client'),  # Riders edit client details


]
