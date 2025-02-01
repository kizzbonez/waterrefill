from django.urls import path
from .views import ProductListCreateView, ProductDetailView

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
]
