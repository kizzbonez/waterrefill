from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from payments.models import Payment
from orders.models import Order
from api.serializers.payments import PaymentSerializer
from django.contrib.auth.models import User

class ClientPaymentView(APIView):
    """
    Clients can:
    - Add a payment
    - View their payment history
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Retrieve all payments made by the authenticated client """
        payments = Payment.objects.filter(order_id__customer=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """ Allow a client to add a payment """
        data = request.data
        order_id = data.get("order_id")

        # Check if the order exists and belongs to the client
        try:
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or does not belong to you"}, status=status.HTTP_404_NOT_FOUND)

        # Create the payment
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RiderPaymentView(APIView):
    """
    Riders can:
    - View payments by order ID or customer user ID
    - Create a payment for an order they are assigned to
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Retrieve payments based on order_id or customer_id """
        order_id = request.query_params.get("order_id")
        customer_id = request.query_params.get("customer_id")

        if order_id:
            payments = Payment.objects.filter(order_id=order_id)
        elif customer_id:
            try:
                customer = User.objects.get(id=customer_id)
            except User.DoesNotExist:
                return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
            
            payments = Payment.objects.filter(order_id__customer=customer)
        else:
            return Response({"error": "Please provide order_id or customer_id"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """ Allow a rider to add a payment for an order they are assigned to """
        data = request.data
        order_id = data.get("order_id")

        # Check if the order exists and is assigned to the rider
        try:
            order = Order.objects.get(id=order_id, assigned_to=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or not assigned to you"}, status=status.HTTP_404_NOT_FOUND)

        # Create the payment
        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
