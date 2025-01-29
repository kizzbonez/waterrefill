from django.db import models

from django.contrib.auth.models import AbstractUser
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        (0, 'Client'),
        (1, 'Rider'),
        (2, 'Admin'),
    )

    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=0)
    firebase_tokens = models.TextField(default="") # store the firebase tokens of the user
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # New Field
    address = models.TextField(blank=True, null=True)  # New Field
    long =  models.CharField(max_length=20, blank=True, null=True)  # New Field
    lat =  models.CharField(max_length=20, blank=True, null=True)  # New Field
    # if your additional field is a required field, just add it, don't forget to add 'email' field too.
    REQUIRED_FIELDS = ['user_type']



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