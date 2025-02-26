from celery import shared_task
from admin_portal.models import CustomUser
from orders.models import Order
from django.core.exceptions import ObjectDoesNotExist

@shared_task
def send_reminder(customer_id):
    try:
        customers = CustomUser.objects.filter(
            user_type=0
        ).exclude(firebase_tokens__isnull=True).exclude(firebase_tokens="")

        for customer in customers:
            print(f"User ID: {customer.id}, Email: {customer.email}, Tokens: {customer.firebase_tokens}")

        print("Test Prinit Schedule")
       
    except ObjectDoesNotExist:
        print(f"Customer with ID {customer_id} not found.")
    except Exception as e:
        print(f"Error sending reminder to customer {customer_id}: {e}")
