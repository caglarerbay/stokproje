# inventory/views_api.py (isteğe bağlı, ayrı bir dosya oluşturabilirsin; ya da mevcut views.py içine ekleyebilirsin)
from rest_framework import generics, permissions
from .models import Product
from .serializers import ProductSerializer
from .models import UserStock
from .serializers import UserStockSerializer
from .models import StockTransaction
from .serializers import StockTransactionSerializer
from rest_framework.permissions import AllowAny

# Ürünleri listeleyen view
class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # Böylece kimlik doğrulaması istemeyecek

# Yeni ürün ekleme için (POST işlemi)
class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserStockListAPIView(generics.ListAPIView):
    serializer_class = UserStockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Sadece o an giriş yapmış kullanıcının stokları
        return UserStock.objects.filter(user=self.request.user)

class StockTransactionListAPIView(generics.ListAPIView):
    queryset = StockTransaction.objects.all().order_by('-timestamp')
    serializer_class = StockTransactionSerializer
    permission_classes = [permissions.IsAdminUser]  # Sadece admin görebilsin, isteğe bağlı