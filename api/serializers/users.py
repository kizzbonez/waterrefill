from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()  # Get the correct user model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Ensure this is set correctly
        fields = ['id', 'username', 'email', 'first_name', 'last_name','groups']