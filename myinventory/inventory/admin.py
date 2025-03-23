from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Product, UserStock, StockTransaction, DailyAccessCode
from .models import AppSettings

User = get_user_model()

# Önce unregister edelim
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass  # eğer zaten unregister durumundaysa hata vermez

# Şimdi inline tanımlayalım
class UserStockInline(admin.TabularInline):
    model = UserStock
    extra = 0

@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    inlines = [UserStockInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # "id" eklenince, admin listesinde "ID" sütunu görünür
    list_display = ('part_code', 'name', 'quantity', 'min_limit', 'order_placed', 'id')
    search_fields = ('part_code', 'name')

# Eğer UserStock'ı ayrı kaydetmek istemiyorsan, kaydetme:
# @admin.register(UserStock)  # YORUM SATIRINA AL
# class UserStockAdmin(admin.ModelAdmin):
#     list_display = ('user', 'product', 'quantity')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'transaction_type', 'product', 'quantity', 'user', 'target_user')
    list_filter = ('transaction_type', 'timestamp')

@admin.register(DailyAccessCode)
class DailyAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('date', 'code')


# admin.py


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "critical_stock_email", "export_stock_email")

    # Tek satır tutmak istiyorsanız, 
    # "add" butonunu kapatmak veya "singleton" yaklaşımı uygulamak için 
    # override edebilirsiniz. Ama basit haliyle bu da iş görür.
