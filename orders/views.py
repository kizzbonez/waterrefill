from rest_framework import generics, status
from rest_framework.response import Response
from .models import Order, OrderDetails
from .serializers import OrderSerializer, OrderDetailsSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    """
    Handles listing all orders and creating a new order with order details.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        """Custom creation method to handle nested OrderDetails"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting an order.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def update(self, request, *args, **kwargs):
        """Custom update method to handle updating nested OrderDetails"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailsListCreateView(generics.ListCreateAPIView):
    """
    Handles listing all order details and creating a new order detail.
    """
    queryset = OrderDetails.objects.all()
    serializer_class = OrderDetailsSerializer

class OrderDetailsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting an order detail.
    """
    queryset = OrderDetails.objects.all()
    serializer_class = OrderDetailsSerializer
