from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm
from .models import DailyAccessCode
from django.contrib.auth.decorators import login_required

from .models import Product, UserStock, StockTransaction
from .forms import TakeProductForm, ReturnProductForm, TransferProductForm, UseProductForm, ProductAddForm
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.core.mail import send_mail
from django.conf import settings
from .reports import create_excel_report
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .models import AppSettings







@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"detail": "Kullanıcı adı ve şifre zorunludur."},
                        status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        staff_flag = user.is_staff
        return Response({
            "detail": "Giriş başarılı.",
            "is_staff": staff_flag
        }, status=200)
    else:
        return Response({"detail": "Geçersiz kullanıcı adı veya şifre."},
                        status=status.HTTP_400_BAD_REQUEST)





@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    JSON bekliyoruz:
    {
      "username": "ali",
      "email": "ali@example.com",
      "access_code": "1234567890",
      "password": "ali12345",
      "password2": "ali12345"  // Opsiyonel, eğer doğrulama istiyorsan
    }
    """
    # 1) Gerekli verileri al
    username = request.data.get('username')
    email = request.data.get('email')
    access_code = request.data.get('access_code')
    password = request.data.get('password')
    password2 = request.data.get('password2')  # opsiyonel

    # 2) Boş alan kontrolü
    if not username or not email or not access_code or not password:
        return Response({"detail": "Tüm alanlar zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Şifre doğrulama (opsiyonel)
    if password2 and password != password2:
        return Response({"detail": "Parolalar eşleşmiyor."}, status=status.HTTP_400_BAD_REQUEST)

    # 4) Günlük kodu kontrolü
    today = timezone.now().date()
    try:
        daily_code = DailyAccessCode.objects.get(date=today)
        if daily_code.code != access_code:
            return Response({"detail": "Geçersiz erişim kodu."}, status=status.HTTP_400_BAD_REQUEST)
    except DailyAccessCode.DoesNotExist:
        return Response({"detail": "Bugün için erişim kodu belirlenmedi."}, status=status.HTTP_400_BAD_REQUEST)

    # 5) Kullanıcı adı veya email zaten var mı?
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Bu kullanıcı adı zaten mevcut."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "Bu email adresi zaten kullanılıyor."}, status=status.HTTP_400_BAD_REQUEST)

    # 6) Kullanıcı oluşturma
    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    return Response({"detail": "Kayıt başarılı."}, status=status.HTTP_201_CREATED)



@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_user(request):
    """
    JSON bekliyoruz:
    {
      "username": "ali",
      "access_code": "1234567890",
      "new_password": "yeniSifre",
      "new_password2": "yeniSifre"
    }
    1) username + daily code eşleşiyor mu?
    2) new_password2 ile doğrulama
    3) user set_password(new_password)
    4) kaydet
    """
    username = request.data.get('username')
    access_code = request.data.get('access_code')
    new_password = request.data.get('new_password')
    new_password2 = request.data.get('new_password2')

    # 1) Boş alan kontrolü
    if not username or not access_code or not new_password or not new_password2:
        return Response({"detail": "Tüm alanlar zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

    # 2) Parola doğrulama
    if new_password != new_password2:
        return Response({"detail": "Yeni şifreler eşleşmiyor."}, status=status.HTTP_400_BAD_REQUEST)

    # 3) Günlük kodu kontrolü
    today = timezone.now().date()
    try:
        daily_code = DailyAccessCode.objects.get(date=today)
        if daily_code.code != access_code:
            return Response({"detail": "Geçersiz erişim kodu."}, status=status.HTTP_400_BAD_REQUEST)
    except DailyAccessCode.DoesNotExist:
        return Response({"detail": "Bugün için erişim kodu belirlenmedi."}, status=status.HTTP_400_BAD_REQUEST)

    # 4) Kullanıcıyı bul
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Kullanıcı bulunamadı."}, status=status.HTTP_400_BAD_REQUEST)

    # 5) Şifreyi güncelle
    user.set_password(new_password)
    user.save()

    return Response({"detail": "Şifre başarıyla güncellendi."}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_product(request):
    """
    GET /api/search_product/?q=...
    1) 'q' parametresi boş ise 400 döner.
    2) Ürünleri part_code veya name içinde arar.
    3) Her ürün için 'car_stocks' listesi ekler, 
       orada kullanıcı adı ve quantity bilgisi gösterir.
    4) Eğer sonuç yoksa boş liste döndürür (200).
    """
    query = request.GET.get('q', '').strip()
    if not query:
        # Arama terimi boşsa 400 döndürelim
        return Response({"detail": "Arama terimi boş olamaz."}, status=status.HTTP_400_BAD_REQUEST)

    products = Product.objects.filter(
        Q(part_code__icontains=query) | Q(name__icontains=query)
    )

    results = []
    for p in products:
        # Bu ürün ana depodaki miktar:
        main_stock_qty = p.quantity

        # Kullanıcı stoklarını bulalım:
        user_stocks = UserStock.objects.filter(product=p)
        # Her user_stock için { "username": ..., "quantity": ... }
        car_stocks_list = []
        for us in user_stocks:
            car_stocks_list.append({
                "username": us.user.username,
                "quantity": us.quantity
            })

        results.append({
            "id": p.id,
            "part_code": p.part_code,
            "name": p.name,
            "quantity": main_stock_qty,  # Ana stok miktarı
            "car_stocks": car_stocks_list  # Bu ürünü tutan kullanıcıların stoğu
        })

    # Eğer products boşsa results da boş olur. 200 döndürür, Flutter bunu işleyebilir.
    return Response(results, status=status.HTTP_200_OK)



@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])  # Sadece admin görebilsin
def critical_stock_api(request):
    """
    GET /api/critical_stock_api/
    quantity <= min_limit olan ürünleri JSON döndürür.
    """
    from django.db.models import F
    critical_products = Product.objects.filter(quantity__lte=F('min_limit'))

    results = []
    for p in critical_products:
        results.append({
            "id": p.id,
            "part_code": p.part_code,
            "name": p.name,
            "quantity": p.quantity,
            "min_limit": p.min_limit,
            "order_placed": p.order_placed
        })

    return Response({"critical_products": results}, status=200)




@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """
    GET /api/user_list/
    Tüm kullanıcıların kullanıcı adlarını JSON olarak döndürür.
    """
    from django.contrib.auth.models import User
    users = User.objects.all()
    results = []
    for u in users:
        results.append(u.username)

    return Response({"users": results}, status=200)



@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Kullanıcı token veya session ile doğrulanmalı
def my_stock(request):
    """
    GET /api/my_stock/
    Kullanıcının stoğunu JSON olarak döndürür.
    """
    # Artık sabit testuser yerine, token'dan gelen user
    user = request.user
    # (İsteğe bağlı) if not user.is_authenticated: check
    # Ama 'IsAuthenticated' zaten 401 döndürecek

    user_stocks = UserStock.objects.filter(user=user)

    results = []
    for us in user_stocks:
        results.append({
            "product_id": us.product.id,
            "part_code": us.product.part_code,
            "product_name": us.product.name,
            "quantity": us.quantity
        })

    return Response({"stocks": results}, status=status.HTTP_200_OK)





@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductAddForm(request.POST)
        if form.is_valid():
            part_code = form.cleaned_data['part_code']
            name = form.cleaned_data['name']
            qty = form.cleaned_data['quantity']

            product, created = Product.objects.get_or_create(
                part_code=part_code,
                defaults={'name': name, 'quantity': qty}
            )

            if not created:
                product.quantity += qty
                product.save()

                # Eğer ürün güncellendiğinde sipariş çekilmişse, sıfırlıyoruz.
                if product.order_placed:
                    product.order_placed = False
                    product.save()

                StockTransaction.objects.create(
                    product=product,
                    transaction_type="UPDATE",
                    quantity=qty,
                    user=request.user,
                    description="Var olan ürüne ekleme yapıldı.",
                    current_quantity=product.quantity
                )
            else:
                StockTransaction.objects.create(
                    product=product,
                    transaction_type="IN",
                    quantity=qty,
                    user=request.user,
                    description="Yeni ürün eklendi.",
                    current_quantity=product.quantity
                )
            return redirect("index")
    else:
        form = ProductAddForm()
    return render(request, "inventory/add_product.html", {"form": form})

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .models import Product, UserStock, StockTransaction
from django.contrib.auth.models import User


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_user_stocks(request):
    """
    GET /api/admin_list_user_stocks/
    Opsiyonel: ?username=caglar
    
    Eğer ?username=caglar verilirse, sadece "caglar" kullanıcısının stoğunu döndürür.
    Aksi halde tüm kullanıcıları döndürür.
    
    Örnek yanıt:
    {
      "user_stocks": [
        {
          "username": "caglar",
          "stocks": [
            { "product_id": 5, "part_code": "ABC", "quantity": 10 },
            ...
          ]
        },
        ...
      ]
    }
    """
    from django.contrib.auth.models import User
    
    # 1) Opsiyonel sorgu parametresi
    username_filter = request.GET.get('username', None)

    # 2) Tüm kullanıcıları çek
    users = User.objects.all().order_by('username')
    
    # 3) Eğer username parametresi varsa, o kullanıcıyı filtrele
    if username_filter:
        users = users.filter(username=username_filter)
        # Eğer hiç kullanıcı bulamadıysak, 200 döner ama "user_stocks":[] olabilir
        # İsterseniz 404 döndürmeyi tercih edebilirsiniz. Tamamen size bağlı.

    result = []
    for u in users:
        user_stocks = UserStock.objects.filter(user=u)
        stocks_data = []
        for us in user_stocks:
            stocks_data.append({
                "product_id": us.product.id,
                "part_code": us.product.part_code,
                "quantity": us.quantity
            })
        
        result.append({
            "username": u.username,
            "stocks": stocks_data
        })

    return Response({"user_stocks": result}, status=200)



@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_adjust_user_stock(request):
    """
    POST /api/admin_adjust_user_stock/
    Body: {
      "username": "kemal",
      "part_code": "ABC",
      "new_quantity": 5
    }

    Admin, kullanıcının stoğunu manuel ayarlar.
    Eger new_quantity=0 ise stoğu tamamen kaldırabiliriz (delete).
    """
    data = request.data
    username = data.get('username')
    part_code = data.get('part_code')
    new_quantity = data.get('new_quantity', None)

    # 1) Zorunlu alan kontrolü
    if not username or not part_code or new_quantity is None:
        return Response({"detail": "username, part_code, new_quantity zorunlu."}, status=400)

    try:
        new_quantity = int(new_quantity)
    except ValueError:
        return Response({"detail": "new_quantity sayı olmalı."}, status=400)

    # 2) Kullanıcıyı bul
    from django.contrib.auth.models import User
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Hedef kullanıcı bulunamadı."}, status=400)

    # 3) Ürünü bul
    product = Product.objects.filter(part_code=part_code).first()
    if not product:
        return Response({"detail": "Ürün bulunamadı (part_code hatalı?)."}, status=400)

    # 4) Kullanıcı stoğu bul
    user_stock = UserStock.objects.filter(user=target_user, product=product).first()
    old_quantity = 0
    if user_stock:
        old_quantity = user_stock.quantity

    if new_quantity <= 0:
        # 0 veya negatif => stoğu tamamen kaldır
        if user_stock:
            user_stock.delete()

        # Transaction kaydı: ADMIN_ADJUST (Kaldırma)
        StockTransaction.objects.create(
            product=product,
            transaction_type="ADMIN_ADJUST",
            quantity=0,  # veya abs(old_quantity)
            user=request.user,  # admin
            target_user=target_user,
            description=f"Admin stok manuel silme. Eski: {old_quantity}, Yeni: 0",
            current_user_quantity=0
        )

        return Response({
            "detail": "Kullanıcının stoğu kaldırıldı.",
            "old_quantity": old_quantity,
            "new_quantity": 0
        }, status=200)
    else:
        # new_quantity > 0 => set
        if not user_stock:
            # stoğu yoksa oluştur
            user_stock = UserStock.objects.create(user=target_user, product=product, quantity=new_quantity)
        else:
            user_stock.quantity = new_quantity
            user_stock.save()

        # Transaction kaydı: ADMIN_ADJUST
        # Burada isterseniz quantity=new_quantity yerine fark da tutabilirsiniz
        StockTransaction.objects.create(
            product=product,
            transaction_type="ADMIN_ADJUST",
            quantity=new_quantity,  # set edilen miktar
            user=request.user,  # admin
            target_user=target_user,
            description=f"Admin stok manuel ayarlama. Eski: {old_quantity}, Yeni: {new_quantity}",
            current_user_quantity=new_quantity
        )

        return Response({
            "detail": "Kullanıcının stoğu ayarlandı.",
            "old_quantity": old_quantity,
            "new_quantity": new_quantity
        }, status=200)





@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_add_product(request):
    """
    POST /api/admin_add_product/
    Body: { "part_code":"ABC", "name":"Deneme", "quantity":5, "min_limit":10 } (opsiyonel)
    """
    data = request.data
    part_code = data.get('part_code')
    name = data.get('name')
    qty = data.get('quantity', 0)
    # Opsiyonel min_limit, yoksa 0
    min_limit = data.get('min_limit', 0)

    # parse integer
    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "quantity geçersiz"}, status=400)

    try:
        min_limit = int(min_limit)
    except ValueError:
        return Response({"detail": "min_limit geçersiz"}, status=400)

    # Ürün zaten varsa hata ver (yalnızca yeni ekleme için)
    if Product.objects.filter(part_code=part_code).exists():
        return Response({"detail": "Bu part_code zaten mevcut. Stok güncelleme kullanın."}, status=400)

    # Yeni ürün oluştur
    product = Product.objects.create(
        part_code=part_code,
        name=name,
        quantity=qty,
        min_limit=min_limit
    )

    # Transaction kaydı: NEW_PRODUCT
    StockTransaction.objects.create(
        product=product,
        transaction_type="IN",
        quantity=qty,
        user=request.user,
        description="Yeni ürün eklendi (admin_add_product).",
        current_quantity=product.quantity
    )

    return Response({
        "detail": "Yeni ürün eklendi.",
        "part_code": part_code,
        "quantity": qty,
        "min_limit": min_limit
    }, status=200)



@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_update_stock(request, product_id):
    """
    POST /api/admin_update_stock/<product_id>/
    Body: { "arrived_quantity": 10 }

    Var olan ürüne siparişle gelen miktarı ekler.
    Eğer product.order_placed=True ise sıfırlar (false yapar).
    """
    data = request.data
    arrived_qty = data.get('arrived_quantity', None)

    if arrived_qty is None:
        return Response({"detail": "arrived_quantity alanı zorunlu."}, status=400)

    try:
        arrived_qty = int(arrived_qty)
    except ValueError:
        return Response({"detail": "arrived_quantity sayı olmalı."}, status=400)

    product = get_object_or_404(Product, id=product_id)

    old_qty = product.quantity
    product.quantity += arrived_qty
    # Sipariş gelince order_placed'ı sıfırlayalım
    if product.order_placed:
        product.order_placed = False

    product.save()

    # Transaction kaydı
    StockTransaction.objects.create(
        product=product,
        transaction_type="UPDATE",  # veya "ARRIVED" diyebilirsiniz
        quantity=arrived_qty,
        user=request.user,  # admin
        description=f"Admin stok güncellemesi. Eski: {old_qty}, Yeni: {product.quantity}",
        current_quantity=product.quantity
    )

    return Response({
        "detail": "Stok güncellendi, sipariş bilgisi sıfırlandı.",
        "old_quantity": old_qty,
        "new_quantity": product.quantity
    }, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_update_min_limit(request, product_id):
    """
    POST /api/admin_update_min_limit/<product_id>/
    Body: { "new_min_limit": 10 }
    """
    data = request.data
    new_min_limit = data.get('new_min_limit', None)

    if new_min_limit is None:
        return Response({"detail": "new_min_limit alanı zorunlu."}, status=400)

    try:
        new_min_limit = int(new_min_limit)
    except ValueError:
        return Response({"detail": "new_min_limit sayı olmalı."}, status=400)

    product = get_object_or_404(Product, id=product_id)
    old_limit = product.min_limit
    product.min_limit = new_min_limit
    product.save()

    return Response({
        "detail": "min_limit güncellendi.",
        "old_min_limit": old_limit,
        "new_min_limit": new_min_limit,
        "product_id": product.id,
        "product_part_code": product.part_code
    }, status=200)






@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Artık kimlik doğrulama gerekli
def take_product(request, product_id):
    """
    JSON tabanlı alma işlemi:
    POST /take_product/<product_id>/
    Body: { "quantity": 3 }

    Bu fonksiyon, ana depodan car stoğuna ürün alır.
    Kullanıcı token (veya session) ile istek yapmalı, request.user'a göre işlem yapılır.
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    # Ana stokta yeterli var mı?
    if product.quantity < qty:
        return Response({"detail": "Ana stokta yeterli miktar yok."}, status=status.HTTP_400_BAD_REQUEST)

    # Token'dan gelen kullanıcı
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Kullanıcı doğrulanmadı."}, status=status.HTTP_401_UNAUTHORIZED)

    # Kullanıcının stoğunu bul veya oluştur
    user_stock, created = UserStock.objects.get_or_create(user=user, product=product)
    user_stock.quantity += qty
    user_stock.save()

    product.quantity -= qty
    product.save()

    StockTransaction.objects.create(
        product=product,
        transaction_type="TAKE",
        quantity=qty,
        user=user,
        description="Kullanıcı ana stoktan ürün aldı.",
        current_quantity=product.quantity,
        current_user_quantity=user_stock.quantity
    )

    return Response({"detail": "Alma işlemi başarılı"}, status=status.HTTP_200_OK)



@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Artık kimlik doğrulama gerekli
def return_product(request, product_id):
    """
    JSON tabanlı iade işlemi:
    POST /return_product/<product_id>/
    Body: { "quantity": 2 }

    Bu fonksiyon, car stoğundan ana stoğa ürün iade eder.
    Kullanıcı token ile istek yapmalı (request.user).
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    # Artık sabit "testuser" yerine, token'dan gelen kullanıcıyı alıyoruz
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Kullanıcı doğrulanmadı."}, status=status.HTTP_401_UNAUTHORIZED)

    # Kullanıcının stoğunu bul
    user_stock = UserStock.objects.filter(user=user, product=product).first()
    if not user_stock or user_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=status.HTTP_400_BAD_REQUEST)

    user_stock.quantity -= qty
    user_stock.save()

    product.quantity += qty
    product.save()

    StockTransaction.objects.create(
        product=product,
        transaction_type="RETURN",
        quantity=qty,
        user=user,
        description="Kullanıcı ürünü ana stoğa iade etti.",
        current_quantity=product.quantity,
        current_user_quantity=user_stock.quantity
    )

    return Response({"detail": "Bırakma işlemi başarılı"}, status=status.HTTP_200_OK)





@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Artık kimlik doğrulaması gerekli
def transfer_product_api(request, product_id):
    """
    JSON tabanlı transfer:
    POST /transfer_product/<product_id>/
    Body: { "quantity": 2, "target_username": "kemal" }

    Bu fonksiyon, kullanıcı stoğundan başka bir kullanıcıya ürün transfer eder.
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)
    target_username = data.get('target_username', '')

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    # Artık sabit "testuser" yok, token'dan gelen kullanıcı (transferi başlatan)
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Kullanıcı doğrulanmadı."}, status=status.HTTP_401_UNAUTHORIZED)

    # Gönderen stoğu
    sender_stock = UserStock.objects.filter(user=user, product=product).first()
    if not sender_stock or sender_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=status.HTTP_400_BAD_REQUEST)

    # Hedef kullanıcıyı bul
    try:
        target_user = User.objects.get(username=target_username)
    except User.DoesNotExist:
        return Response({"detail": "Hedef kullanıcı bulunamadı."}, status=status.HTTP_400_BAD_REQUEST)

    # Hedef stoğu bul veya oluştur
    receiver_stock, created = UserStock.objects.get_or_create(user=target_user, product=product)

    # Transfer miktarını düş - ekle
    sender_stock.quantity -= qty
    sender_stock.save()

    receiver_stock.quantity += qty
    receiver_stock.save()

    # İşlem kaydı
    StockTransaction.objects.create(
        product=product,
        transaction_type="TRANSFER",
        quantity=qty,
        user=user,  # Transferi başlatan
        target_user=target_user,
        description="Kullanıcılar arası transfer (JSON).",
        current_user_quantity=sender_stock.quantity,
        current_receiver_quantity=receiver_stock.quantity
    )

    return Response({"detail": "Transfer işlemi başarılı"}, status=status.HTTP_200_OK)




@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Token veya session kimlik doğrulaması gereksin
def use_product_api(request, product_id):
    """
    JSON tabanlı kullanım:
    POST /use_product/<product_id>/
    Body: { "quantity": 2 }

    Bu fonksiyon, car stoğundan ürünü kullanma (düşme) işlemi yapar.
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    # Artık sabit "testuser" yok, token'dan gelen kullanıcı
    user = request.user
    if not user.is_authenticated:
        return Response({"detail": "Kullanıcı doğrulanmadı."}, status=status.HTTP_401_UNAUTHORIZED)

    # Kullanıcının stoğunu bul
    user_stock = UserStock.objects.filter(user=user, product=product).first()
    if not user_stock or user_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=status.HTTP_400_BAD_REQUEST)

    # Kullanım işlemi: stoktan qty kadar düş
    user_stock.quantity -= qty
    user_stock.save()

    # İşlem kaydı (StockTransaction)
    StockTransaction.objects.create(
        product=product,
        transaction_type="USE",
        quantity=qty,
        user=user,
        description="Kullanıcı ürünü kullandı (JSON).",
        current_user_quantity=user_stock.quantity
    )

    return Response({"detail": "Kullanım işlemi başarılı"}, status=status.HTTP_200_OK)




@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])  # Sadece admin (is_staff=True) erişebilsin
def transaction_log_api(request):
    """
    GET /api/transaction_log_api/
    
    Tüm stok hareketlerini (StockTransaction) JSON olarak döndürür.
    Son oluşturulan en üstte gelecek şekilde timestamp'e göre sıralıyoruz.
    """
    logs = StockTransaction.objects.all().order_by('-timestamp')
    results = []

    for log in logs:
        results.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),  # isoformat() => "2025-03-24T14:30:00.123456"
            "transaction_type": log.transaction_type,
            "product_code": log.product.part_code if log.product else None,
            "quantity": log.quantity,
            "user": log.user.username if log.user else None,
            "target_user": log.target_user.username if log.target_user else None,
            "description": log.description,
            "current_quantity": log.current_quantity,
            "current_user_quantity": log.current_user_quantity,
            "current_receiver_quantity": log.current_receiver_quantity,
        })

    return Response({"logs": results}, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])  # Sadece admin (is_staff=True) erişebilsin
def admin_update_app_settings(request):
    """
    POST /api/admin_update_app_settings/
    Body: { "recipient_email": "yeniadres@example.com" }

    Bu fonksiyon, AppSettings tablosundaki mail adresini günceller
    (veya hiç yoksa oluşturur).
    """
    data = request.data
    new_email = data.get("recipient_email", None)

    if not new_email:
        return Response({"detail": "recipient_email alanı zorunlu."}, status=400)

    # Örnek: email formatını kontrol etmek isterseniz (isteğe bağlı)
    # from django.core.validators import validate_email
    # try:
    #     validate_email(new_email)
    # except:
    #     return Response({"detail": "Geçersiz email formatı."}, status=400)

    # AppSettings modelini import et
    from .models import AppSettings
    app_settings = AppSettings.objects.first()

    if not app_settings:
        # Eğer hiç kayıt yoksa, yeni bir tane oluşturuyoruz
        app_settings = AppSettings.objects.create(recipient_email=new_email)
        created = True
    else:
        # Varsa güncelliyoruz
        old_email = app_settings.recipient_email
        app_settings.recipient_email = new_email
        app_settings.save()
        created = False

    return Response({
        "detail": "Ayarlar güncellendi." if not created else "Ayarlar oluşturuldu.",
        "recipient_email": app_settings.recipient_email
    }, status=200)







@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_excel_report_email_api(request):
    from django.db.models import F
    critical_products = Product.objects.filter(quantity__lte=F('min_limit'))
    if not critical_products.exists():
        return Response({"detail": "Kritik stok ürünü bulunamadı. Mail gönderilmeyecek."}, status=400)

    # create_excel_report, mail gövdesi vs. aynen
    excel_file = create_excel_report(critical_products)
    excel_content = excel_file.read()
    excel_file.seek(0)

    # Alıcı: app_settings.critical_stock_email
    from .models import AppSettings
    app_settings = AppSettings.objects.first()
    if app_settings and app_settings.critical_stock_email:
        recipient_email = app_settings.critical_stock_email
    else:
        recipient_email = "nuk.stoktakip@gmail.com"  # fallback

    email = EmailMessage(
        "Kritik Stok Excel Raporu",
        "Ek'te kritik stok raporunu bulabilirsiniz.",
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )
    # Dosya adında tarih eklemek isterseniz
    from django.utils import timezone
    date_str = timezone.now().strftime("%d-%m-%Y")
    filename = f"kritik_stok_raporu_{date_str}.xlsx"
    email.attach(filename, excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()

    # order_placed=True update vb.

    return Response({"detail": "Kritik stok Excel raporu maili gönderildi."}, status=200)




@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_full_stock_report_api(request):
    """
    POST /api/send_full_stock_report/
    Tek bir mailde:
      - Ana stok (ana_stok_{tarih}.xlsx)
      - Her kullanıcının stoğu ({username}_stok_{tarih}.xlsx) 
    şeklinde çoklu ek gönderir.
    Alıcı -> AppSettings.export_stock_email
    """
    from django.utils import timezone
    from django.contrib.auth.models import User
    from .reports import create_excel_for_products, create_excel_for_single_user

    # 1) Tarih (gün-ay-yıl)
    current_date_str = timezone.now().strftime("%d-%m-%Y")

    # 2) Ana stok verisi
    products = Product.objects.all()
    excel_file_products = create_excel_for_products(products)
    content_products = excel_file_products.read()
    ana_stok_filename = f"ana_stok_{current_date_str}.xlsx"

    # 3) Tüm kullanıcılar
    users = User.objects.all().order_by('username')

    # 4) Mail alıcısı (export_stock_email)
    app_settings = AppSettings.objects.first()
    if app_settings and app_settings.export_stock_email:
        recipient_email = app_settings.export_stock_email
    else:
        recipient_email = "fallback@example.com"

    # 5) Mail oluştur
    email = EmailMessage(
        subject="Tüm Stok Raporu",
        body="Ek'te ana stok ve her kullanıcının stoğu ayrı Excel dosyalarında yer almaktadır.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email]
    )

    # 6) Ana stok ekini ekle
    email.attach(
        ana_stok_filename,
        content_products,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 7) Her kullanıcı için ayrı Excel ekle
    for u in users:
        user_stocks = UserStock.objects.filter(user=u)
        if not user_stocks.exists():
            # Boş stoğu olan kullanıcı için Excel oluşturmak istemiyorsanız continue diyebilirsiniz.
            continue

        excel_file_user = create_excel_for_single_user(u, user_stocks)
        content_user = excel_file_user.read()

        user_filename = f"{u.username}_stok_{current_date_str}.xlsx"
        email.attach(
            user_filename,
            content_user,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 8) Mail gönder
    email.send()

    return Response({"detail": "Ana stok ve kullanıcı stokları ayrı Excel dosyalarında gönderildi."}, status=200)









#push test fonsksiyonu silinecek
from django.http import HttpResponse
from .reports import send_push_notification
def test_push(request):
    result = send_push_notification("Test Başlık", "Bu bir test push bildirimi.")
    return HttpResponse(f"Push notification result: {result}")
