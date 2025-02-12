"""
Unit Tests for API Endpoints

This test suite contains API tests for user-related, product-related, and payment-related functionality, including:
- Retrieving and updating user information
- User registration
- Editing client details as a rider
- Viewing client lists as a rider
- Password reset functionality
- Listing and retrieving product details
- Viewing and adding client payments
- Viewing and adding rider payments

Tested API Endpoints:
- `/api/v1/user/` (User Info)
- `/api/v1/register/` (User Registration)
- `/api/v1/rider/edit-client/{id}/` (Rider Editing Client Info)
- `/api/v1/rider/all-client/` (Rider Viewing All Clients)
- `/api/v1/password-reset/request/` (Password Reset Request)
- `/api/v1/password-reset/confirm/` (Password Reset Confirmation)
- `/api/v1/products/` (List all products)
- `/api/v1/products/{id}/` (Retrieve product details)
- `/api/v1/payments/` (Client payments)
- `/api/v1/rider/payments/` (Rider payments)

"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api.serializers.users import UserSerializer
from api.serializers.products import ProductSerializer
from api.serializers.payments import PaymentSerializer
from products.models import Product
from payments.models import Payment
from orders.models import Order, OrderDetails

User = get_user_model()

class PaymentTests(APITestCase):
    """Tests for client and rider payments."""
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="clientuser",
            email="client@example.com",
            password="password123",
            user_type=0
        )
        self.client_user2 = User.objects.create_user(
            username="clientuse2r",
            email="client2@example.com",
            password="password123",
            user_type=0
        )
        self.rider_user = User.objects.create_user(
            username="rideruser",
            email="rider@example.com",
            password="password123",
            user_type=1
        )
        self.product = Product.objects.create(name="Test Product", price=100.00)
        self.order = Order.objects.create(customer=self.client_user)
        self.order_detail = OrderDetails.objects.create(order=self.order, product=self.product, total_price=500.00, quantity=2)
        self.payment = Payment.objects.create(order_id=self.order, amount=500.00)
        self.client = APIClient()
    
    def authenticate_user(self, user):
        """Authenticate a given user for testing protected routes."""
        self.client.force_authenticate(user=user)
    
    def test_client_view_payments(self):
        """Ensure clients can view their own payment history."""
        self.authenticate_user(self.client_user)
        response = self.client.get("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_client_add_payment(self):
        """Ensure clients can add a payment and a product must be selected."""
        self.authenticate_user(self.client_user)
        response = self.client.post("/api/v1/payments/", {"order_id": self.order.id, "amount": 250.00})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_rider_view_payments(self):
        """Ensure riders can view payments by order ID or customer ID."""
        self.authenticate_user(self.rider_user)
        response = self.client.get(f"/api/v1/rider/payments/?order_id={self.order.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rider_add_payment(self):
        """Ensure riders can add a payment for an order they are assigned to."""
        self.authenticate_user(self.rider_user)
        response = self.client.post("/api/v1/rider/payments/", {"order_id": self.order.id, "amount": 100.00})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_payment_not_found(self):
        """Ensure 404 is returned when querying a non-existent payment."""
        self.authenticate_user(self.client_user)
        response = self.client.get("/api/v1/payments/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_to_make_payment_for_others_order(self):
        """Ensure 404 is returned when querying a non-existent payment."""
        self.authenticate_user(self.client_user2)
        response = self.client.post("/api/v1/rider/payments/", {"order_id": self.order.id, "amount": 100.00})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
