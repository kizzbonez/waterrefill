"""
Unit Tests for User API Endpoints

This test suite contains API tests for user-related functionality, including:
- Retrieving and updating user information
- User registration
- Editing client details as a rider
- Viewing client lists as a rider
- Password reset functionality

Tested API Endpoints:
- `/api/v1/user/` (User Info)
- `/api/v1/register/` (User Registration)
- `/api/v1/rider/edit-client/{id}/` (Rider Editing Client Info)
- `/api/v1/rider/all-client/` (Rider Viewing All Clients)
- `/api/v1/password-reset/request/` (Password Reset Request)
- `/api/v1/password-reset/confirm/` (Password Reset Confirmation)

"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api.serializers.users import UserSerializer

User = get_user_model()

class UserTests(APITestCase):
    """Tests for retrieving and updating user profile information."""
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="clientuser",  
            email="client@example.com",
            password="password123",
            user_type=0
        )
        self.rider_user = User.objects.create_user(
            username="rideruser",  
            email="rider@example.com",
            password="password123",
            user_type=1
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="admin123", username="superuser", user_type=2
        )
        self.client = APIClient()

    def authenticate_user(self, user):
        """Authenticate a given user for testing protected routes."""
        self.client.force_authenticate(user=user)
    
    def test_user_info_get_authenticated(self):
        """Ensure authenticated users can retrieve their profile information."""
        self.authenticate_user(self.client_user)
        response = self.client.get("/api/v1/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.client_user.email)

    def test_user_info_get_unauthenticated(self):
        """Ensure unauthenticated users receive a 401 response."""
        response = self.client.get("/api/v1/user/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_info_update_valid(self):
        """Ensure clients can successfully update their own profile."""
        self.authenticate_user(self.client_user)
        response = self.client.post("/api/v1/user/", {"first_name": "New Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "New Name")
    
    def test_user_info_update_permission_denied(self):
        """Ensure users without permission cannot update another user's profile."""
        self.authenticate_user(self.rider_user)
        response = self.client.post("/api/v1/user/", {"first_name": "New Name"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class UserRegistrationTests(APITestCase):
    """Tests for user registration functionality."""
    def setUp(self):
        self.client = APIClient()
    
    def test_register_valid_user(self):
        """Ensure a user can successfully register."""
        response = self.client.post("/api/v1/register/", {
            "email": "newuser@example.com",
            "user_type": 0,
            "password": "password",
            "confirm_password": "password",
            "username": "newuser"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_register_invalid_user(self):
        """Ensure invalid registration requests return 400 errors."""
        response = self.client.post("/api/v1/register/", {"email": "", "password": "password123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class RiderEditClientTests(APITestCase):
    """Tests for riders editing client information."""
    def setUp(self):
        self.rider = User.objects.create_user(email="rider@example.com", password="password123", user_type=1, username="rideruser")
        self.client_user = User.objects.create_user(email="client@example.com", password="password123", user_type=0, username="clientuser")
        self.client = APIClient()
    
    def test_rider_can_edit_client(self):
        """Ensure riders can edit client information."""
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(f"/api/v1/rider/edit-client/{self.client_user.id}/", {"first_name": "Updated Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_rider_cannot_edit_client(self):
        """Ensure non-riders cannot edit client information."""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(f"/api/v1/rider/edit-client/{self.client_user.id}/", {"first_name": "Updated Name"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class RiderClientListViewTests(APITestCase):
    """Tests for riders retrieving a list of clients."""
    def setUp(self):
        self.rider = User.objects.create_user(email="rider@example.com", user_type=1, password="password", username="rider")
        User.objects.create_user(email="newuser2@example.com", user_type=0, password="password", username="newuser2")
        User.objects.create_user(email="newuser@example.com", user_type=0, password="password", username="newuser")
        self.client = APIClient()
    
    def test_rider_can_view_clients(self):
        """Ensure riders can view a list of clients."""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get("/api/v1/rider/all-client/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_non_rider_cannot_view_clients(self):
        """Ensure non-riders cannot access the client list."""
        normal_user = User.objects.create_user(email="normal@example.com", password="password123", user_type=0, username="normaluser")
        self.client.force_authenticate(user=normal_user)
        response = self.client.get("/api/v1/rider/all-client/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
