from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order, OrderDetails
from api.serializers.orders import OrderSerializer, OrderDetailsSerializer
from products.models import Product  # Ensure Product model exists
from django.contrib.auth import get_user_model
from django.db import transaction
User = get_user_model()  # Get the correct user model
class OrderListCreateView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(customer=user) | Order.objects.filter(assigned_to=user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """ Create an order, but reject it if it contains inactive products. """
        assigned_to_id = request.data.get("assigned_to")  # Get assigned_to from request

        serializer = OrderSerializer(data=request.data)
        
        if serializer.is_valid():
            # ✅ Ensure assigned_to is saved correctly
            assigned_to_user = None
            if assigned_to_id:
                try:
                    assigned_to_user = User.objects.get(id=assigned_to_id)
                except User.DoesNotExist:
                    return Response({"error": f"User with ID {assigned_to_id} not found."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Create the order first
            order = serializer.save(customer=request.user, assigned_to=assigned_to_user)

            # ✅ Process order details
            order_details_data = request.data.get('order_details', [])
            for detail in order_details_data:
                product_id = detail.get("product")
                quantity = detail.get("quantity")

                try:
                    product = Product.objects.get(id=product_id)
                    if not product.status:  # ❌ Reject order if product is inactive
                        order.delete()  # Rollback order creation
                        return Response({"error": f"Product '{product.name}' is not available."}, status=status.HTTP_400_BAD_REQUEST)

                except Product.DoesNotExist:
                    order.delete()  # Rollback order creation if product doesn't exist
                    return Response({"error": f"Product with ID {product_id} not found."}, status=status.HTTP_400_BAD_REQUEST)

                OrderDetails.objects.create(order=order, product=product, quantity=quantity)

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class OrderDetailView(APIView):
    """
    View for retrieving, updating, and deleting an order using POST.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """ Handle updating an order and reducing stock when delivered. """
        try:
            order = Order.objects.get(pk=pk)

            # 🔹 Ensure the user is authorized
            if order.customer != request.user and order.assigned_to != request.user:
                return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

            action = request.data.get("action")

            if action == "update":
                """ Update the order if action='update' """
                order_data = request.data
                order_details_data = order_data.get('order_details', [])  # Extract order details
                serializer = OrderSerializer(order, data=order_data, partial=True)
                
                if serializer.is_valid():
                    with transaction.atomic():
                        updated_order = serializer.save()

                        # Handle order details update
                        for detail in order_details_data:
                            detail_id = detail.get("id", None)
                            product_id = detail.get("product")
                            quantity = detail.get("quantity")

                            if detail_id:
                                # Update existing order detail
                                try:
                                    order_detail = OrderDetails.objects.get(id=detail_id, order=order)
                                    order_detail.quantity = quantity
                                    order_detail.product_id = product_id
                                    order_detail.save()
                                except OrderDetails.DoesNotExist:
                                    return Response({"error": f"Order detail with ID {detail_id} not found."},
                                                    status=status.HTTP_404_NOT_FOUND)
                            else:
                                # Ensure product exists before creating a new order detail
                                try:
                                    product = Product.objects.get(id=product_id)
                                except Product.DoesNotExist:
                                    return Response({"error": f"Product with ID {product_id} not found."},
                                                    status=status.HTTP_400_BAD_REQUEST)

                                # Create new order detail
                                OrderDetails.objects.create(order=order, product=product, quantity=quantity)

                        # ✅ Reduce product quantity if status is "Delivered" (status=4)
                        if updated_order.status == 4 or updated_order.status == 8:
                            for order_detail in OrderDetails.objects.filter(order=updated_order):
                                product = order_detail.product
                                if product.stock >= order_detail.quantity:
                                    product.stock -= order_detail.quantity
                                    product.save()
                                else:
                                    return Response(
                                        {"error": f"Not enough stock for product {product.name}"},
                                        status=status.HTTP_400_BAD_REQUEST
                                    )

                    return Response({"message": "Order updated successfully", "order": serializer.data}, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            elif action == "delete":
                """ Delete the order if action='delete' """
                order.delete()
                return Response({"message": "Order deleted successfully"}, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid action. Use 'update' or 'delete'."}, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
