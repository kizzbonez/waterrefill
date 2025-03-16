
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
    (5, 'Chargeback'),    # Payment was disputed and reversed
    (6, 'On Hold'),       # Payment is temporarily held for verification
    (7, 'Processing'),    # Payment is being processed (e.g., bank transfer)
    (8, 'Partially Paid'),# A part of the payment has been received
    (9, 'Awaiting Payment'), # Payment is expected but not received yet
    (10, 'Authorized'),   # Payment is authorized but not yet captured
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

            if self.amount > remaining_balance:
                raise ValidationError(f"Cannot save. Payment exceeds remaining balance. Remaining: {remaining_balance:.2f}")

        super().save(*args, **kwargs)
def __str__(self):
    return f"Payment {self.id} - {self.get_status_display()} ({self.ref_code or 'No Ref'})"
