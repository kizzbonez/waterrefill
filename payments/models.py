
# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
class Payment(models.Model):

    PAYMENT_STATUS_CHOICES = (
    (0, 'Pending'),       # Payment has not been received yet
    (1, 'Completed'),     # Payment has been successfully received
    (2, 'Failed'),        # Payment attempt was unsuccessful
    (3, 'Cancelled'),     # Payment was canceled by the user or system
    (4, 'Refunded'),      # Payment has been refunded to the customer
    )

    
    PAYMENT_METHOD_CHOICES = (
    (0, 'Cash'),       #  For Cash Payment
    (1, 'Gcash'),     # For Gcash Payment
    (2, 'Bank Transfer'),  # For Bank Transfer Payment
    (3, 'Other'),  # For Other type of payment
    )


    ref_code = models.CharField(max_length=255,null=True, blank=True)
    order_id = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(choices=PAYMENT_STATUS_CHOICES, default=0)
    payment_method = models.IntegerField(choices=PAYMENT_METHOD_CHOICES, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Prevent multiple payments that exceed the total order amount"""
        if self.order_id:
            total_order_amount = self.order_id.get_total_amount()
            previous_payments = Payment.objects.filter(order_id=self.order_id).aggregate(Sum('amount'))['amount__sum'] or 0
            remaining_balance = total_order_amount - previous_payments
           

        super().save(*args, **kwargs)
def __str__(self):
    return f"Payment {self.id} - {self.get_status_display()} ({self.ref_code or 'No Ref'})"
