from django.urls import path
from .views_api import (
    ProductListAPIView,
    ProductCreateAPIView,
    UserStockListAPIView,
    StockTransactionListAPIView,
)

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='api-product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='api-product-create'),
    path('user-stocks/', UserStockListAPIView.as_view(), name='api-user-stocks'),
    path('transactions/', StockTransactionListAPIView.as_view(), name='api-transactions'),
]
