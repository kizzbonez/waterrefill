from rest_framework import serializers

class LogoutSerializer(serializers.ModelSerializer):
    token = serializers.CharField()

    def validate_token(self, value):
        """Optional: Validate token format"""
        if not value.startswith("ey"):  # JWT tokens usually start with 'ey...'
            raise serializers.ValidationError("Invalid token format")
        return value
