from django.urls import path
from .views import PaymenttListCreateView, PaymentDetailView

urlpatterns = [
    path('payments/', PaymenttListCreateView.as_view(), name='payment_list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
]
