from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

class BaseTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Base serializer to handle authentication and token response.
    """
    user_type_required = None  # Set this in subclasses

    def validate(self, attrs):
        username, password = attrs.get("username"), attrs.get("password")

        # Authenticate user
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        # Ensure user has the required user type (if set)
        if self.user_type_required is not None and getattr(user, 'user_type', None) != self.user_type_required:
            raise AuthenticationFailed(f"Only {'riders' if self.user_type_required == 1 else 'clients'} can log in here.")

        self.user = user  # Assign authenticated user
        data = super().validate(attrs)

        # Add expiration timestamps
        refresh = self.get_token(user)
        data.update({
            "access_expires": datetime.fromtimestamp(refresh.access_token.payload['exp']).isoformat(),
            "refresh_expires": datetime.fromtimestamp(refresh.payload['exp']).isoformat()
        })

        return data


class CustomTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    """
    Serializer for customer (client) login, restricted to `user_type=0`.
    """
    user_type_required = 0


class RiderTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    """
    Serializer for rider login, restricted to `user_type=1`.
    """
    user_type_required = 1
