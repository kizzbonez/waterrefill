# Generated by Django 4.2.18 on 2025-03-14 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetails',
            name='current_product_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
