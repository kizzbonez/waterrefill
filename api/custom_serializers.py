from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime
from rest_framework_simplejwt.settings import api_settings

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add expiration time to the response
        refresh = self.get_token(self.user)
        data['access_expires'] = datetime.fromtimestamp(refresh.access_token.payload['exp']).isoformat()
        data['refresh_expires'] = datetime.fromtimestamp(refresh.payload['exp']).isoformat()

        return data
