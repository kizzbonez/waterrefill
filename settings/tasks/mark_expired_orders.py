from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from orders.models import Order
from payments.models import Payment

@shared_task(name="settings.tasks.mark_expired_orders")
def mark_expired_orders():
    try:
        threshold = timezone.now() - timedelta(hours=24)

        expired_orders = Order.objects.filter(
            created_at__lt=threshold,
            status__in=[0, 1, 2, 3],  # Update based on your "active" statuses
        ).exclude(
            id__in=Payment.objects.values_list('order_id', flat=True)
        )

        count = expired_orders.update(status=9)
        print(f"{count} expired order(s) marked with status 9.")
        return count
    except Exception as e:
        print(f"Error while marking expired orders: {e}")
        return 0