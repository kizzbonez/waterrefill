from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from datetime import timedelta
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

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'address',
            'long', 'lat', 'user_type', 'password', 'confirm_password'
        ]
        extra_kwargs = {
            'user_type': {'read_only': True},  # Prevent clients from modifying user_type
        }

    def validate(self, data):
        """ Ensure password and confirm_password match """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """ Remove confirm_password before saving """
        validated_data.pop('confirm_password')
        validated_data['user_type'] = 0  # Force user_type to be 0 (client)
        user = User.objects.create_user(**validated_data)  # Automatically hashes password
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """ Check if email exists in the system """
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")
        return value

    def save(self):
        """ Generate reset token and send email """
        user = self.user
        user.set_reset_token()  # Generate token

        # Send email with reset link
        reset_link = f"{user.reset_token}"
        send_mail(
            subject="Password Reset Request",
            message=f"Copy the reset token :\n\n{reset_link}",
            from_email="noreply@yourdomain.com",
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        """ Validate token and ensure passwords match """
        try:
            self.user = User.objects.get(reset_token=data["token"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        if not self.user.is_reset_token_valid():
            raise serializers.ValidationError({"token": "Reset token has expired."})

        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return data

    def save(self):
        """ Reset user's password """
        user = self.user
        user.set_password(self.validated_data["new_password"])  # Hash new password
        user.clear_reset_token()  # Clear token
        user.save()

        return user