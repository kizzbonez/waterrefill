"""
Unit Tests for API Endpoints

This test suite contains API tests for user-related and product-related functionality, including:
- Retrieving and updating user information
- User registration
- Editing client details as a rider
- Viewing client lists as a rider
- Password reset functionality
- Listing and retrieving product details

Tested API Endpoints:
- `/api/v1/user/` (User Info)
- `/api/v1/register/` (User Registration)
- `/api/v1/rider/edit-client/{id}/` (Rider Editing Client Info)
- `/api/v1/rider/all-client/` (Rider Viewing All Clients)
- `/api/v1/password-reset/request/` (Password Reset Request)
- `/api/v1/password-reset/confirm/` (Password Reset Confirmation)
- `/api/v1/products/` (List all products)
- `/api/v1/products/{id}/` (Retrieve product details)

"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api.serializers.users import UserSerializer
from api.serializers.products import ProductSerializer
from products.models import Product

User = get_user_model()

class ProductTests(APITestCase):
    """Tests for retrieving product lists and product details."""
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="clientuser",
            email="client@example.com",
            password="password123",
            user_type=0
        )
        self.product1 = Product.objects.create(name="Product 1", description="Description 1", price=100.00)
        self.product2 = Product.objects.create(name="Product 2", description="Description 2", price=200.00)
        self.client = APIClient()
    
    def authenticate_user(self, user):
        """Authenticate a given user for testing protected routes."""
        self.client.force_authenticate(user=user)
    
    def test_product_list_authenticated(self):
        """Ensure authenticated users can retrieve the product list."""
        self.authenticate_user(self.client_user)
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_product_list_unauthenticated(self):
        """Ensure unauthenticated users receive a 401 response when accessing products."""
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_product_detail_authenticated(self):
        """Ensure authenticated users can retrieve a single product detail."""
        self.authenticate_user(self.client_user)
        response = self.client.get(f"/api/v1/products/{self.product1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Product 1")
    
    def test_product_detail_not_found(self):
        """Ensure 404 is returned when requesting a non-existent product."""
        self.authenticate_user(self.client_user)
        response = self.client.get("/api/v1/products/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_product_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot retrieve product details."""
        response = self.client.get(f"/api/v1/products/{self.product1.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
