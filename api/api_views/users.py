from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from api.serializers.users import UserSerializer, UserRegistrationSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()  # Get the correct user model

class UserInfoView(APIView):
    """ View for Clients to update their own profile """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user or user.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user

        if not user or user.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type != 0:  # Only allow clients
            return Response({"error": "Permission denied. Only clients can update their profile."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()  # Copy request data to modify it safely

        # ✅ Allow password update
        if "password" in data:
            user.password = make_password(data["password"])

        # ❌ Prevent user_type modification
        data.pop("user_type", None)  # Remove user_type from request data

        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
    """
    API endpoint for user (customer) registration.
    """

    def post(self, request):
        """ Allow new customers to register. """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully!", "user": serializer.data}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RiderEditClientView(APIView):
    """ View for Riders to edit Client details """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        rider = request.user

        # 🔹 Ensure the rider is authenticated and has the correct role
        if not rider or rider.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if rider.user_type != 1:  # Only riders can access this endpoint
            return Response({"error": "Permission denied. Only riders can edit client details."}, status=status.HTTP_403_FORBIDDEN)

        # 🔹 Fetch the client, if exists
        try:
            client = User.objects.get(id=user_id, user_type=0)  # Only update clients
        except User.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        # 🔹 Serialize and update the client profile
        serializer = UserSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RiderClientListView(APIView):
    """ View for Riders to edit Client details """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        rider = request.user

        # 🔹 Ensure the rider is authenticated and has the correct role
        if not rider or rider.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if rider.user_type != 1:  # Only riders can access this endpoint
            return Response({"error": "Permission denied. Only riders can edit client details."}, status=status.HTTP_403_FORBIDDEN)

        # 🔹 Fetch the client, if exists
        try:
            client = User.objects.get(id=user_id, user_type=0)  # Only update clients
        except User.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        # 🔹 Serialize and update the client profile
        serializer = UserSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RiderClientListView(APIView):
    """ View for Riders to view client list and edit client details """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Retrieve a list of clients """
        rider = request.user

        # 🔹 Ensure the rider is authenticated and has the correct role
        if not rider or rider.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if rider.user_type != 1:  # Only riders can access this endpoint
            return Response({"error": "Permission denied. Only riders can view clients."}, status=status.HTTP_403_FORBIDDEN)

        # 🔹 Fetch all clients (users with user_type=0)
        clients = User.objects.filter(user_type=0)
        serializer = UserSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """ Handles password reset token generation and email sending """

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """ Handles actual password reset using token """

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RiderClientDetailView(APIView):
    """ View for Client Info """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
       
        rider = request.user
        # 🔹 Ensure the rider is authenticated and has the correct role
        if not rider or rider.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if rider.user_type != 1:  # Only riders can access this endpoint
            return Response({"error": "Permission denied. Only riders can view clients."}, status=status.HTTP_403_FORBIDDEN)
        user = User.objects.get(pk=user_id,user_type=0)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)