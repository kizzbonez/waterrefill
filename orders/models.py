from django.db import models
from django.db.models.signals import post_save, m2m_changed ,pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import Sum

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'Preparing'),
        (2, 'On Hold'),
        (3, 'On the way'),
        (4, 'Delivered'),
        (8, 'Completed'),
        (5, 'Cancelled By Client'),
        (6, 'Cancelled By Rider'),
        (7, 'Cancelled by Admin'),
        (9, 'Cancelled - 24hrs Limit Reach'),
    )
    assigned_to = models.ForeignKey(
        'admin_portal.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_orders'
    )
    customer = models.ForeignKey(
        'admin_portal.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='customer_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_datetime = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.IntegerField(choices=ORDER_STATUS_CHOICES, default=0)
    def get_status_display(self):
        """✅ Helper function to return the status as text"""
        return dict(self.ORDER_STATUS_CHOICES).get(self.status, "Unknown")
    def get_total_amount(self):
        """✅ Calculate total amount based on order details"""
        return sum(item.total_price  for item in self.order_details.all())
    def __str__(self):
        return f"Order #{self.id} - {self.customer.last_name if self.customer else 'N/A'} , {self.customer.first_name if self.customer else ''}".strip()

class OrderDetails(models.Model):
    class Meta:
        verbose_name = "Order Detail"
        verbose_name_plural = "Order Details"



    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_details')
    current_product_price =  models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='order_details', null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)  # Default to 1 instead of 0

    def save(self, *args, **kwargs):
        """Automatically updates total price before saving."""
        if self.product and self.quantity:
              # Check if this is an update and compare product_id
            if self.pk:  # This means the instance is already saved before
                existing_instance = OrderDetails.objects.filter(pk=self.pk).first()
                if existing_instance and existing_instance.product_id != self.product_id:
                    self.current_product_price = self.product.price  # Update price when product changes
            #if curren_product_price is not None, then use it to calculate total price
            if self.current_product_price:
                self.total_price = self.current_product_price * self.quantity
            else:
                self.total_price = self.product.price * self.quantity  # Ensure correct total price
            # Store the current price of the product for first save
            if not self.current_product_price:
                self.current_product_price = self.product.price


          
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