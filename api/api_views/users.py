from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.serializers.users import UserSerializer


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
