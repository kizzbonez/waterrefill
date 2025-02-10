from django.db import models

class StoreSettings(models.Model):
    store_name = models.CharField(max_length=255, verbose_name="Store Name")
    login_header_message = models.TextField(blank=True, null=True, verbose_name="Login Header Message")
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True, verbose_name="Logo")
    favicon = models.ImageField(upload_to="favicons/", blank=True, null=True, verbose_name="Favicon")
    timezone = models.CharField(max_length=100, default="UTC", verbose_name="Timezone")
    currency = models.CharField(max_length=10, default="USD", verbose_name="Currency")
    currency_symbol = models.CharField(max_length=5, default="$", verbose_name="Currency Symbol")
    store_latitude = models.CharField(max_length=20, blank=True, null=True, verbose_name="Store Latitude")  
    store_longitude = models.CharField(max_length=20, blank=True, null=True, verbose_name="Store Longitude")  
    gmap_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Google Maps API Key")
    firebase_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Firebase API Key")
    firebase_auth_domain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Firebase Auth Domain")
    
    def save(self, *args, **kwargs):
        self.pk = 1  # Force only one instance
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion

    @classmethod
    def get_instance(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return "Store Settings"

    class Meta:
        verbose_name = "Store Setting"
        verbose_name_plural = "Store Settings"
