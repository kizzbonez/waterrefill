from rest_framework import serializers
from .models import Order, OrderDetails

class OrderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True)  # Nested Serializer

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        order_details_data = validated_data.pop('order_details', [])
        order = Order.objects.create(**validated_data)
        for detail_data in order_details_data:
            OrderDetails.objects.create(order=order, **detail_data)
        return order

    def update(self, instance, validated_data):
        order_details_data = validated_data.pop('order_details', [])
        instance.user_type = validated_data.get('user_type', instance.user_type)
        instance.assigned_to = validated_data.get('assigned_to', instance.assigned_to)
        instance.customer = validated_data.get('customer', instance.customer)
        instance.save()

        # Update or Create OrderDetails
        for detail_data in order_details_data:
            detail_id = detail_data.get('id', None)
            if detail_id:
                # Update existing order detail
                order_detail = OrderDetails.objects.get(id=detail_id, order=instance)
                for attr, value in detail_data.items():
                    setattr(order_detail, attr, value)
                order_detail.save()
            else:
                # Create new order detail
                OrderDetails.objects.create(order=instance, **detail_data)

        return instance
