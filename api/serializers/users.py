from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the correct user model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'groups',
            'user_permissions', 'is_staff', 'is_active', 'is_superuser',
            'last_login', 'date_joined', 'phone_number', 'address', 'long', 'lat', 'user_type'
        ]

    def update(self, instance, validated_data):
        """
        Custom update method to prevent certain fields from being modified
        when a rider is updating a client's profile.
        """
        request = self.context.get('request', None)

        if request and request.user.user_type == 1:  # If the user is a rider
            restricted_fields = {'username', 'email', 'is_staff', 'is_active', 'is_superuser', 'user_type'}
            for field in restricted_fields:
                validated_data.pop(field, None)  # Remove these fields to prevent unauthorized updates

        return super().update(instance, validated_data)
