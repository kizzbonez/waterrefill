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
    - Edit a payment using POST (if payment_id is provided)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """ Retrieve all payments made by the authenticated client """
        payments = Payment.objects.filter(order_id__customer=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """ Create or update a payment for the client """
        data = request.data
        payment_id = data.get("payment_id")
        order_id = data.get("order_id")

        if payment_id:
            # Update existing payment
            try:
                payment = Payment.objects.get(id=payment_id, order_id__customer=request.user)
            except Payment.DoesNotExist:
                return Response({"error": "Payment not found or does not belong to you"}, status=status.HTTP_404_NOT_FOUND)

            serializer = PaymentSerializer(payment, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Create a new payment
            try:
                order = Order.objects.get(id=order_id, customer=request.user)
            except Order.DoesNotExist:
                return Response({"error": "Order not found or does not belong to you"}, status=status.HTTP_404_NOT_FOUND)

            serializer = PaymentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class RiderPaymentGetView(APIView):
    """
    Riders can:
    - View payments by order ID or customer user ID
    """
    permission_classes = [IsAuthenticated]

    def get(self, request,id):
        """ Retrieve payments based on order_id or customer_id """
        order_id = id
 
        if order_id:
            payments = Payment.objects.filter(order_id=order_id)
        else:
            return Response({"error": "Please provide order_id"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RiderPaymentView(APIView):
    """
    Riders can:
    - Create or edit a payment using POST
    """

    def post(self, request):
        """ Create or update a payment for a rider """
        data = request.data
        payment_id = data.get("payment_id")
        order_id = data.get("order_id")

        if payment_id:
            # Update existing payment
            try:
                payment = Payment.objects.get(id=payment_id, order_id__assigned_to=request.user)
            except Payment.DoesNotExist:
                return Response({"error": "Payment not found or not assigned to you"}, status=status.HTTP_404_NOT_FOUND)

            serializer = PaymentSerializer(payment, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Create a new payment
            try:
                order = Order.objects.get(id=order_id, assigned_to=request.user)
            except Order.DoesNotExist:
                return Response({"error": "Order not found or not assigned to you"}, status=status.HTTP_404_NOT_FOUND)

            serializer = PaymentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
