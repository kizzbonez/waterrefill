from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("Logout request received")  # Debugging print
        from api.models import BlacklistedToken
        try:
            # Get the access token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith("Bearer "):
                print("No access token provided")  # Debugging print
                return Response({"error": "No access token provided"}, status=status.HTTP_400_BAD_REQUEST)

            access_token = auth_header.split(" ")[1]  # Extract token
            print(f"Extracted token: {access_token}")  # Debugging print

            token = AccessToken(access_token)  # Validate token
            print("Token validated")  # Debugging print

            # Blacklist the token
            BlacklistedToken.objects.create(token=str(token))
            print("Token blacklisted successfully")  # Debugging print

            return Response({"message": "User logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            print(f"Error during logout: {str(e)}")  # Debugging print
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
