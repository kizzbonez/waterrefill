from django.db import models

# Create your models here.
from django.db import models

class Product(models.Model):
    PRODUCT_STATUS_CHOICES = (
        (True, 'Active'),
        (False, 'Inactive')
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    cost = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    water_product = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    status = models.BooleanField(choices=PRODUCT_STATUS_CHOICES, default=True)
    stock_alert_level = models.IntegerField(default=0)


    def __str__(self):
        return self.name
