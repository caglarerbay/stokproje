from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
# Ürün modelimiz: ana stokta yer alan parçalar.

class Product(models.Model):
    part_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    
    # Varsayılan olarak 0, yani quantity <= 0 olursa kritik stok.
    min_limit = models.PositiveIntegerField(
        default=0,
        help_text="Bu değer 0 ise ürün adedi 0 olduğunda kritik stok sayılır. "
                  "Eğer 5 gibi bir değer girilirse ürün adedi 5 veya altına düştüğünde kritik stok sayılır."
    )
    
    order_placed = models.BooleanField(
        default=False, 
        help_text="Bu ürün için sipariş çekildiyse True olur."
    )


    image = models.ImageField(
        upload_to='product_images/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.part_code} - {self.name}"





# Kullanıcı stoklarını tutan model
class UserStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="user_stocks")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.part_code} : {self.quantity}"


# Stok hareketlerinin loglanması için model
class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Ana Stok Girişi'),
        ('UPDATE', 'Ana Stok Güncelleme'),
        ('TAKE', 'Kullanıcının Ana Stoktan Alması'),
        ('RETURN', 'Kullanıcının Ana Stoka İade Etmesi'),
        ('TRANSFER', 'Kullanıcılar Arası Transfer'),
        ('USE', 'Kullanım'),
        ('ADJUST', 'Admin Stok Ayarı'),
        ('O_TRANSFER', 'Diğer Transfer'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_transactions")
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    # Ana stok için güncel miktar:
    current_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="İşlem sonrası ana stok miktarı")
    # İşlem yapan kullanıcının stoğunda kalan miktar (örneğin TAKE, RETURN, USE işlemlerinde):
    current_user_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="İşlem sonrası kullanıcının stoğundaki miktar")
    # Transfer işleminde, alıcı kullanıcının stoğundaki güncel miktar:
    current_receiver_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Transfer işleminde alıcının stoğundaki miktar")

    def __str__(self):
        return f"{self.transaction_type} - {self.product.part_code} - {self.quantity}"



# Günlük 10 haneli kodu tutan model (bu kod admin tarafından güncellenip her gün değişecek)
class DailyAccessCode(models.Model):
    code = models.CharField(max_length=10)
    date = models.DateField(unique=True)

    def __str__(self):
        return f"{self.date} - {self.code}"

#telefona gidecek olan bildirimler
class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_token}"


# models.py



class AppSettings(models.Model):
    # Kritik stok raporunun gideceği adres
    critical_stock_email = models.EmailField(
        default="kritik@example.com",
        help_text="Kritik stok raporu bu mail adresine gönderilecek."
    )
    # Dışa aktar (tüm stok) raporunun gideceği adres
    export_stock_email = models.EmailField(
        default="export@example.com",
        help_text="Tüm stok raporu bu mail adresine gönderilecek."
    )

    def __str__(self):
        return "Uygulama Ayarları"

