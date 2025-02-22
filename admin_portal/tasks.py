# myapp/tasks.py
from celery import shared_task
import datetime

@shared_task
def my_scheduled_task():
    now = datetime.datetime.now()
    print(f"Scheduled Task Executed at: {now}")
    return f"Task ran at {now}"
