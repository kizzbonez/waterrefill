from django.db import models

class BlacklistedToken(models.Model):
    token = models.CharField(max_length=500, unique=True)  # Store JWT access token
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of blacklisting

    def __str__(self):
        return f"Blacklisted token {self.token} - {self.created_at}"
