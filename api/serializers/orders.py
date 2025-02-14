from rest_framework import serializers
from orders.models import Order, OrderDetails
from products.models import Product
from django.contrib.auth import get_user_model
from settings.models import StoreSettings # ✅ Import Setting model

User = get_user_model()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'lat', 'long']

class OrderDetailsSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderDetails
        fields = ['id', 'product', 'quantity', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)  # ✅ Full customer details
    assigned_to = UserSerializer(read_only=True)  # ✅ Full assigned_to details
    order_details = OrderDetailsSerializer(many=True, read_only=True)  # ✅ Full order details
    customer_lat = serializers.SerializerMethodField()
    customer_long = serializers.SerializerMethodField()
    store_lat = serializers.SerializerMethodField()
    store_long = serializers.SerializerMethodField()
    

    class Meta:
        model = Order
        fields = ['id', 'customer', 'assigned_to', 'status', 'delivery_datetime', 'remarks', 'order_details', 'customer_lat', 'customer_long', 'store_lat', 'store_long']

    def get_customer_lat(self, obj):
        """ Fetch latitude from the customer model """
        return obj.customer.lat if obj.customer else None

    def get_customer_long(self, obj):
        """ Fetch longitude from the customer model """
        return obj.customer.long if obj.customer else None

    def get_store_lat(self, obj):
        """ Fetch store latitude from the Setting model """
        setting = StoreSettings.objects.first()  # ✅ Assuming a single settings row exists
        return setting.store_latitude if setting else None

    def get_store_long(self, obj):
        """ Fetch store longitude from the Setting model """
        setting = StoreSettings.objects.first()
        return setting.store_longitude if setting else None
