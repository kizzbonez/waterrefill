from celery import shared_task
from datetime import timedelta
from django.utils.timezone import now
from django.conf import settings
from django.db import models
from admin_portal.models import CustomUser
from orders.models import Order
from settings.utils import send_firebase_notification  # Import utility function

@shared_task(name="settings.tasks.send_reorder_notice")
def send_reorder_notice():
    try:
        # Get the date 3 days ago
        three_days_ago = now() - timedelta(days=3)

        # Find customers whose last order was delivered more than 3 days ago
        customers = CustomUser.objects.filter(
            user_type=0,  # Assuming user_type=0 means customers
            customer_orders__status=4  # Only consider delivered orders
        ).annotate(last_order_date=models.Max('customer_orders__created_at')) \
         .filter(last_order_date__lte=three_days_ago) \
         .exclude(firebase_tokens__isnull=True).exclude(firebase_tokens="")

        # Send push notifications to each customer
        for customer in customers:
            title = "Time to reorder!"
            message = f"Hi {customer.first_name}, it's been a while! Reorder now for fresh delivery."
            token = customer.firebase_tokens  # Ensure this is a valid FCM token (string or list)

            # Send Firebase push notification
            response = send_firebase_notification(title, message, token)
            print(f"Notification sent to {customer.email} → Response: {response}")

        print("Reorder push notifications sent successfully!")

    except Exception as e:
        print(f"Error sending reorder notices: {e}")
