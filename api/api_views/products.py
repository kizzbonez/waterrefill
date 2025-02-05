from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from api.serializers.products import ProductSerializer  # ✅ Import Product serializer
from products.models import Product  # ✅ Import Product model
class ProductListView(generics.ListAPIView):  # ✅ Changed to `ListAPIView` (Only allows `GET`)
    """
    View to list all products.
    - `GET /products/` → List all products (Authenticated users only)
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]  # ✅ Only authenticated users can access
