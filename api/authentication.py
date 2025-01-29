from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        from api.models import BlacklistedToken 
        response = super().authenticate(request)
        if response is None:
            return None

        user, token = response

        # Check if the token is blacklisted
        if BlacklistedToken.objects.filter(token=str(token)).exists():
            raise AuthenticationFailed("This token has been blacklisted. Please log in again.")

        return user, token
