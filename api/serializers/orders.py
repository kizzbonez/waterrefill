from rest_framework import serializers
from orders.models import Order, OrderDetails
from products.models import Product
from django.contrib.auth import get_user_model
User = get_user_model()  # Get the correct user model
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']  # Add any other necessary fields

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email','first_name','last_name','email','phone_number','address','lat','long']  # Customize based on your User model

class OrderDetailsSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # ✅ Show full product details

    class Meta:
        model = OrderDetails
        fields = ['id', 'product', 'quantity', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)  # ✅ Show full customer details
    assigned_to = UserSerializer(read_only=True)  # ✅ Show full assigned_to details
    order_details = OrderDetailsSerializer(many=True, read_only=True)  # ✅ Show full order details

    class Meta:
        model = Order
        fields = ['id', 'customer', 'assigned_to', 'status', 'delivery_datetime', 'remarks', 'order_details']
