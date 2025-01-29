from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.serializers.users import UserSerializer

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users access this

    def get(self, request):
        user = request.user

        # 🔹 Handle cases where user is None
        if not user or user.is_anonymous:
            return Response({"error": "Authentication failed, user not found"}, status=401)

        serializer = UserSerializer(user)
        return Response(serializer.data)
