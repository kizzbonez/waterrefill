# Generated by Django 4.2.18 on 2025-02-01 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_orderdetails_options_orderdetails_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetails',
            name='quantity',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
