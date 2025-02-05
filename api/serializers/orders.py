from rest_framework import serializers
from orders.models import Order, OrderDetails
from products.models import Product  # Ensure Product model exists

class OrderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = ['id', 'product', 'quantity','total_price']

class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True, required=False)  # Make order_details optional

    class Meta:
        model = Order
        fields = ['id', 'customer', 'assigned_to', 'status', 'delivery_datetime', 'remarks', 'order_details']

    def create(self, validated_data):
        order_details_data = validated_data.pop('order_details', [])  # Extract order details
        order = Order.objects.create(**validated_data)

        # # Create OrderDetails (only once)
        # OrderDetails.objects.bulk_create([
        #     OrderDetails(order=order, product=detail_data['product'], quantity=detail_data['quantity'])
        #     for detail_data in order_details_data
        # ])

        return order