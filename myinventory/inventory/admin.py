from django.contrib import admin
from .models import Product, UserStock, StockTransaction, DailyAccessCode

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('part_code', 'name', 'quantity')
    search_fields = ('part_code', 'name')

@admin.register(UserStock)
class UserStockAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity')
    search_fields = ('user__username', 'product__part_code')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'transaction_type', 'product', 'quantity', 'user', 'target_user')
    list_filter = ('transaction_type', 'timestamp')

@admin.register(DailyAccessCode)
class DailyAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('date', 'code')
