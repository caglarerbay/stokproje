from rest_framework import serializers
from .models import Product, UserStock, StockTransaction


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'part_code', 'name', 'quantity', 'min_limit', 'order_placed']


class UserStockSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Ürünü iç içe göstermek için

    class Meta:
        model = UserStock
        fields = ['id', 'user', 'product', 'quantity']



class StockTransactionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    user = serializers.StringRelatedField()  # Kullanıcı adını gösterir
    target_user = serializers.StringRelatedField()

    class Meta:
        model = StockTransaction
        fields = ['id', 'transaction_type', 'product', 'quantity', 'user', 'target_user', 'timestamp', 'description', 'current_quantity', 'current_user_quantity', 'current_receiver_quantity']

