from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from api.serializers.products import ProductSerializer  # ✅ Import Product serializer
from products.models import Product  # ✅ Import Product model
from rest_framework.views import APIView
from rest_framework.response import Response

class ProductListView(generics.ListAPIView):  # ✅ Changed to `ListAPIView` (Only allows `GET`)
    """
    View to list all products.
    - `GET /products/` → List all products (Authenticated users only)
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access
class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """ Retrieve product by ID """
        try:
            product = Product.objects.get(pk=pk)

            serializer =  ProductSerializer(   product )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)