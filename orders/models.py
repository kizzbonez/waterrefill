from django.db import models
from django.db.models.signals import post_save, m2m_changed ,pre_save
from django.dispatch import receiver

class Order(models.Model):
    assigned_to = models.ForeignKey(
        'admin_portal.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_orders'
    )
    customer = models.ForeignKey(
        'admin_portal.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - Customer: {self.customer.username if self.customer else 'N/A'}"

class OrderDetails(models.Model):
    class Meta:
        verbose_name = "Order Detail"
        verbose_name_plural = "Order Details"

    ORDER_STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'Delivered'),
        (2, 'Cancelled'),
    )

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_details')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='order_details', null=False)
    delivery_datetime = models.DateTimeField()
    status = models.IntegerField(choices=ORDER_STATUS_CHOICES, default=0)
    remarks = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)  # Default to 1 instead of 0

    def save(self, *args, **kwargs):
        """Automatically updates total price before saving."""
        if self.product and self.quantity:
            self.total_price = self.product.price * self.quantity  # Ensure correct total price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OrderDetail #{self.pk} - {self.product.name} - Qty: {self.quantity} - Total: {self.total_price}"


@receiver(pre_save, sender=OrderDetails)
def ensure_product_and_quantity(sender, instance, **kwargs):
    """Ensure that product and quantity are provided before saving."""
    if not instance.product:
        raise ValueError("A product must be selected.")
    if instance.quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")