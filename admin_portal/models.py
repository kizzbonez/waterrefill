from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from datetime import timedelta

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, 'Client'),
        (1, 'Rider'),
        (2, 'Admin'),
    )

    email = models.EmailField(unique=True,null=True, blank=True)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=0)
    firebase_tokens = models.TextField(default="")  # Store the Firebase tokens of the user
    phone_number = models.CharField(max_length=15, blank=True, null=True)  
    address = models.TextField(blank=True, null=True)  
    long = models.CharField(max_length=20, blank=True, null=True)  
    lat = models.CharField(max_length=20, blank=True, null=True)  

    # 🔹 Add reset token fields for password reset
    reset_token = models.CharField(max_length=255, blank=True, null=True, unique=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    REQUIRED_FIELDS = ['user_type']

    def set_reset_token(self):
        """ Generate a reset token valid for 1 hour """
        self.reset_token = get_random_string(length=32)  # Generate unique token
        self.reset_token_expiry = now() + timedelta(hours=1)  # Token expires in 1 hour
        self.save()

    def clear_reset_token(self):
        """ Clear reset token after password reset """
        self.reset_token = None
        self.reset_token_expiry = None
        self.save()

    def is_reset_token_valid(self):
        """ Check if the reset token is still valid """
        return self.reset_token and self.reset_token_expiry and self.reset_token_expiry > now()

    def __str__(self):
        return self.username


class ThemeSettings(models.Model):
    site_title = models.CharField(max_length=100, default="My Admin")
    theme = models.CharField(
        max_length=50,
        choices=[
            ("cosmo", "Cosmo"),
            ("darkly", "Darkly"),
            ("flatly", "Flatly"),
            ("cyborg", "Cyborg"),
        ],
        default="cosmo",
    )
    dark_mode_enabled = models.BooleanField(default=False)

    def __str__(self):
        return "Theme Settings"