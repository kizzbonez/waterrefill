from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from api.serializers.products import ProductSerializer  # ✅ Import Product serializer
from products.models import Product  # ✅ Import Product model
from rest_framework.views import APIView
from rest_framework.response import Response

class ProductListView(generics.ListAPIView):
    """
    View to list all active products.
    - `GET /products/` → List only active products (Authenticated users only)
    """
    queryset = Product.objects.filter(status=True)  # ✅ Show only active products
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access

class ProductDetailView(APIView):
    """
    View to retrieve a single active product by ID.
    - `GET /products/{id}/` → Retrieve product details (if active)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """ Retrieve product by ID (only if active) """
        try:
            product = Product.objects.get(pk=pk, status=True)  # ✅ Ensure the product is active
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({"error": "Product not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
