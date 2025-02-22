# Generated by Django 4.2.18 on 2025-02-22 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_remove_orderdetails_delivery_datetime_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Preparing'), (2, 'On Hold'), (3, 'On the way'), (4, 'Delivered'), (5, 'Cancelled By Client'), (6, 'Cancelled By Rider'), (7, 'Cancelled by Admin')], default=0),
        ),
    ]
