from django.urls import path
from .views import generate_sales_report, generate_inventory_report,generate_top_customers_report, generate_top_products_report

urlpatterns = [
    path('download-top-customers-report/', generate_top_customers_report, name="download_test_report"),
    path('download-sales-report/', generate_sales_report, name="download_sales_report"),
    path('download-top-products-report/', generate_top_products_report, name="download_top_products"),
    path('download-inventory-report/', generate_inventory_report, name="download_inventory_report"),

]