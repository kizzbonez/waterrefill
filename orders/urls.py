from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderDetailsListCreateView,
    OrderDetailsDetailView
)

urlpatterns = [
    # Orders API
    path('orders/', OrderListCreateView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),

    # Order Details API
    path('order-details/', OrderDetailsListCreateView.as_view(), name='order_details_list'),
    path('order-details/<int:pk>/', OrderDetailsDetailView.as_view(), name='order_details_detail'),
]
