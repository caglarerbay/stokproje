from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm
from .models import DailyAccessCode, Product, UserStock, StockTransaction, AppSettings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Q
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token

from .reports import create_excel_report, create_excel_for_products, create_excel_for_single_user, send_push_notification


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    POST /api/login/
    Body: { "username": "...", "password": "..." }

    Dönen JSON:
    {
      "detail": "Giriş başarılı.",
      "token": "...",
      "staff_flag": true/false
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {"detail": "Kullanıcı adı ve şifre zorunludur."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)  # Django session opsiyonel

        token, created = Token.objects.get_or_create(user=user)
        staff_flag = user.is_staff

        return Response({
            "detail": "Giriş başarılı.",
            "token": token.key,
            "staff_flag": staff_flag
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {"detail": "Geçersiz kullanıcı adı veya şifre."},
            status=status.HTTP_400_BAD_REQUEST
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    POST /api/register/
    Body: {
      "username": "...",
      "email": "...",
      "access_code": "...",
      "password": "...",
      "password2": "..." (opsiyonel)
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    access_code = request.data.get('access_code')
    password = request.data.get('password')
    password2 = request.data.get('password2')  # opsiyonel

    if not username or not email or not access_code or not password:
        return Response({"detail": "Tüm alanlar zorunludur."}, status=400)

    if password2 and password != password2:
        return Response({"detail": "Parolalar eşleşmiyor."}, status=400)

    today = timezone.now().date()
    try:
        daily_code = DailyAccessCode.objects.get(date=today)
        if daily_code.code != access_code:
            return Response({"detail": "Geçersiz erişim kodu."}, status=400)
    except DailyAccessCode.DoesNotExist:
        return Response({"detail": "Bugün için erişim kodu belirlenmedi."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "Bu kullanıcı adı zaten mevcut."}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "Bu email adresi zaten kullanılıyor."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    return Response({"detail": "Kayıt başarılı."}, status=201)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_user(request):
    """
    POST /api/forgot_password/
    Body: {
      "username": "...",
      "access_code": "...",
      "new_password": "...",
      "new_password2": "..."
    }
    """
    username = request.data.get('username')
    access_code = request.data.get('access_code')
    new_password = request.data.get('new_password')
    new_password2 = request.data.get('new_password2')

    if not username or not access_code or not new_password or not new_password2:
        return Response({"detail": "Tüm alanlar zorunludur."}, status=400)

    if new_password != new_password2:
        return Response({"detail": "Yeni şifreler eşleşmiyor."}, status=400)

    today = timezone.now().date()
    try:
        daily_code = DailyAccessCode.objects.get(date=today)
        if daily_code.code != access_code:
            return Response({"detail": "Geçersiz erişim kodu."}, status=400)
    except DailyAccessCode.DoesNotExist:
        return Response({"detail": "Bugün için erişim kodu belirlenmedi."}, status=400)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Kullanıcı bulunamadı."}, status=400)

    user.set_password(new_password)
    user.save()

    return Response({"detail": "Şifre başarıyla güncellendi."}, status=200)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_product(request):
    """
    GET /api/search_product/?q=...
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({"detail": "Arama terimi boş olamaz."}, status=400)

    products = Product.objects.filter(Q(part_code__icontains=query) | Q(name__icontains=query))

    results = []
    for p in products:
        user_stocks = UserStock.objects.filter(product=p)
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
            "quantity": p.quantity,
            "car_stocks": car_stocks_list
        })

    return Response(results, status=200)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])
def critical_stock_api(request):
    """
    GET /api/critical_stock_api/
    """
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
    """
    users = User.objects.all()
    results = [u.username for u in users]
    return Response({"users": results}, status=200)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stock(request):
    """
    GET /api/my_stock/
    """
    user = request.user
    user_stocks = UserStock.objects.filter(user=user)

    results = []
    for us in user_stocks:
        results.append({
            "product_id": us.product.id,
            "part_code": us.product.part_code,
            "product_name": us.product.name,
            "quantity": us.quantity
        })
    return Response({"stocks": results}, status=200)


@staff_member_required
def add_product(request):
    # (HTML form vs. - eğer kullanmıyorsanız silebilirsiniz)
    pass


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_user_stocks(request):
    """
    GET /api/admin_list_user_stocks/
    Opsiyonel: ?username=caglar
    """
    username_filter = request.GET.get('username', None)
    users = User.objects.all().order_by('username')
    if username_filter:
        users = users.filter(username=username_filter)

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
      "username": "...",
      "part_code": "...",
      "new_quantity": 5
    }
    """
    data = request.data
    username = data.get('username')
    part_code = data.get('part_code')
    new_quantity = data.get('new_quantity', None)

    if not username or not part_code or new_quantity is None:
        return Response({"detail": "username, part_code, new_quantity zorunlu."}, status=400)

    try:
        new_quantity = int(new_quantity)
    except ValueError:
        return Response({"detail": "new_quantity sayı olmalı."}, status=400)

    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "Hedef kullanıcı bulunamadı."}, status=400)

    product = Product.objects.filter(part_code=part_code).first()
    if not product:
        return Response({"detail": "Ürün bulunamadı (part_code hatalı?)."}, status=400)

    user_stock = UserStock.objects.filter(user=target_user, product=product).first()
    old_quantity = 0
    if user_stock:
        old_quantity = user_stock.quantity

    if new_quantity <= 0:
        if user_stock:
            user_stock.delete()
        StockTransaction.objects.create(
            product=product,
            transaction_type="ADMIN_ADJUST",
            quantity=0,
            user=request.user,
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
        if not user_stock:
            user_stock = UserStock.objects.create(user=target_user, product=product, quantity=new_quantity)
        else:
            user_stock.quantity = new_quantity
            user_stock.save()

        StockTransaction.objects.create(
            product=product,
            transaction_type="ADMIN_ADJUST",
            quantity=new_quantity,
            user=request.user,
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
    Body: { "part_code":"...", "name":"...", "quantity":5, "min_limit":10 }
    """
    data = request.data
    part_code = data.get('part_code')
    name = data.get('name')
    qty = data.get('quantity', 0)
    min_limit = data.get('min_limit', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "quantity geçersiz"}, status=400)
    try:
        min_limit = int(min_limit)
    except ValueError:
        return Response({"detail": "min_limit geçersiz"}, status=400)

    if Product.objects.filter(part_code=part_code).exists():
        return Response({"detail": "Bu part_code zaten mevcut. Stok güncelleme kullanın."}, status=400)

    product = Product.objects.create(
        part_code=part_code,
        name=name,
        quantity=qty,
        min_limit=min_limit
    )

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
    if product.order_placed:
        product.order_placed = False
    product.save()

    StockTransaction.objects.create(
        product=product,
        transaction_type="UPDATE",
        quantity=arrived_qty,
        user=request.user,
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
@permission_classes([IsAuthenticated])
def take_product(request, product_id):
    """
    POST /api/take_product/<product_id>/
    Body: { "quantity": 3 }
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)
    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=400)

    if product.quantity < qty:
        return Response({"detail": "Ana stokta yeterli miktar yok."}, status=400)

    user = request.user
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
    return Response({"detail": "Alma işlemi başarılı"}, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_product(request, product_id):
    """
    POST /api/return_product/<product_id>/
    Body: { "quantity": 2 }
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)
    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=400)

    user = request.user
    user_stock = UserStock.objects.filter(user=user, product=product).first()
    if not user_stock or user_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=400)

    user_stock.quantity -= qty
    user_stock.save()

    current_user_qty = user_stock.quantity
    if user_stock.quantity == 0:
        user_stock.delete()
        current_user_qty = 0

    product.quantity += qty
    product.save()

    StockTransaction.objects.create(
        product=product,
        transaction_type="RETURN",
        quantity=qty,
        user=user,
        description="Kullanıcı ürünü ana stoğa iade etti.",
        current_quantity=product.quantity,
        current_user_quantity=current_user_qty
    )
    return Response({"detail": "Bırakma işlemi başarılı"}, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_product_api(request, product_id):
    """
    POST /api/transfer_product/<product_id>/
    Body: { "quantity": 2, "target_username": "kemal" }
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)
    target_username = data.get('target_username', '')

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=400)

    user = request.user
    sender_stock = UserStock.objects.filter(user=user, product=product).first()
    if not sender_stock or sender_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=400)

    try:
        target_user = User.objects.get(username=target_username)
    except User.DoesNotExist:
        return Response({"detail": "Hedef kullanıcı bulunamadı."}, status=400)

    receiver_stock, created = UserStock.objects.get_or_create(user=target_user, product=product)

    sender_stock.quantity -= qty
    sender_stock.save()
    if sender_stock.quantity == 0:
        sender_stock.delete()
        current_sender_qty = 0
    else:
        current_sender_qty = sender_stock.quantity

    receiver_stock.quantity += qty
    receiver_stock.save()

    StockTransaction.objects.create(
        product=product,
        transaction_type="TRANSFER",
        quantity=qty,
        user=user,
        target_user=target_user,
        description="Kullanıcılar arası transfer (JSON).",
        current_user_quantity=current_sender_qty,
        current_receiver_quantity=receiver_stock.quantity
    )
    return Response({"detail": "Transfer işlemi başarılı"}, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_product_api(request, product_id):
    """
    POST /api/use_product/<product_id>/
    Body: { "quantity": 2 }
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)
    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=400)

    user = request.user
    user_stock = UserStock.objects.filter(user=user, product=product).first()
    if not user_stock or user_stock.quantity < qty:
        return Response({"detail": "Kişisel stokta yeterli miktar yok."}, status=400)

    user_stock.quantity -= qty
    user_stock.save()
    current_qty_for_log = user_stock.quantity
    if user_stock.quantity == 0:
        user_stock.delete()
        current_qty_for_log = 0

    StockTransaction.objects.create(
        product=product,
        transaction_type="USE",
        quantity=qty,
        user=user,
        description="Kullanıcı ürünü kullandı (JSON).",
        current_user_quantity=current_qty_for_log
    )
    return Response({"detail": "Kullanım işlemi başarılı"}, status=200)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])
def transaction_log_api(request):
    """
    GET /api/transaction_log_api/
    """
    logs = StockTransaction.objects.all().order_by('-timestamp')
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
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


###
# Aşağıdaki 3 endpoint: admin_get_app_settings, admin_generate_daily_code, admin_update_app_settings
# Ve mail gönderme fonksiyonları
###

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_get_app_settings(request):
    """
    GET /api/admin_get_app_settings/
    Döndürür:
    {
      "critical_stock_email": "...",
      "export_stock_email": "...",
      "daily_code": "..." (bugünün DailyAccessCode kaydı)
    }
    """
    app_settings = AppSettings.objects.first()
    today = timezone.now().date()
    daily_code_obj = DailyAccessCode.objects.filter(date=today).first()
    daily_code_str = daily_code_obj.code if daily_code_obj else ""

    if not app_settings:
        return Response({
            "critical_stock_email": "",
            "export_stock_email": "",
            "daily_code": daily_code_str
        }, status=200)
    else:
        return Response({
            "critical_stock_email": app_settings.critical_stock_email or "",
            "export_stock_email": app_settings.export_stock_email or "",
            "daily_code": daily_code_str
        }, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_generate_daily_code(request):
    """
    POST /api/admin_generate_daily_code/
    Rastgele 10 haneli kod üretir, bugünün DailyAccessCode kaydına yazar.
    Döndürür:
    {
      "detail": "Yeni günlük kod üretildi.",
      "daily_code": "1234567890"
    }
    """
    import random
    import string

    today = timezone.now().date()
    code = ''.join(random.choices(string.digits, k=10))

    daily_code_obj, created = DailyAccessCode.objects.get_or_create(date=today)
    daily_code_obj.code = code
    daily_code_obj.save()

    return Response({
        "detail": "Yeni günlük kod üretildi.",
        "daily_code": code
    }, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_update_app_settings(request):
    """
    POST /api/admin_update_app_settings/
    Body: {
      "critical_stock_email": "...",
      "export_stock_email": "..."
    }
    """
    data = request.data
    critical_email = data.get("critical_stock_email")
    export_email = data.get("export_stock_email")

    if not critical_email or not export_email:
        return Response({"detail": "critical_stock_email ve export_stock_email alanları zorunlu."}, status=400)

    app_settings = AppSettings.objects.first()
    if not app_settings:
        app_settings = AppSettings.objects.create(
            critical_stock_email=critical_email,
            export_stock_email=export_email
        )
        created = True
    else:
        app_settings.critical_stock_email = critical_email
        app_settings.export_stock_email = export_email
        app_settings.save()
        created = False

    return Response({
        "detail": "Ayarlar güncellendi." if not created else "Ayarlar oluşturuldu.",
        "critical_stock_email": app_settings.critical_stock_email,
        "export_stock_email": app_settings.export_stock_email
    }, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_excel_report_email_api(request):
    """
    POST /api/send_excel_report_email_api/
    Kritik stok Excel raporu mail atar.
    """
    from django.db.models import F
    critical_products = Product.objects.filter(quantity__lte=F('min_limit'))
    if not critical_products.exists():
        return Response({"detail": "Kritik stok ürünü bulunamadı. Mail gönderilmeyecek."}, status=400)

    excel_file = create_excel_report(critical_products)
    excel_content = excel_file.read()
    excel_file.seek(0)

    app_settings = AppSettings.objects.first()
    if app_settings and app_settings.critical_stock_email:
        recipient_email = app_settings.critical_stock_email
    else:
        recipient_email = "nuk.stoktakip@gmail.com"

    email = EmailMessage(
        "Kritik Stok Excel Raporu",
        "Ek'te kritik stok raporunu bulabilirsiniz.",
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )
    from django.utils import timezone
    date_str = timezone.now().strftime("%d-%m-%Y")
    filename = f"kritik_stok_raporu_{date_str}.xlsx"
    email.attach(filename, excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()

    return Response({"detail": "Kritik stok Excel raporu maili gönderildi."}, status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_full_stock_report_api(request):
    """
    POST /api/send_full_stock_report/
    Ana stok + her kullanıcının stoğu -> çoklu Excel ek
    """
    from django.utils import timezone
    from django.contrib.auth.models import User

    current_date_str = timezone.now().strftime("%d-%m-%Y")

    products = Product.objects.all()
    excel_file_products = create_excel_for_products(products)
    content_products = excel_file_products.read()
    ana_stok_filename = f"ana_stok_{current_date_str}.xlsx"

    app_settings = AppSettings.objects.first()
    if app_settings and app_settings.export_stock_email:
        recipient_email = app_settings.export_stock_email
    else:
        recipient_email = "fallback@example.com"

    email = EmailMessage(
        "Tüm Stok Raporu",
        "Ek'te ana stok ve kullanıcı stokları yer almaktadır.",
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )

    email.attach(
        ana_stok_filename,
        content_products,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    users = User.objects.all().order_by('username')
    for u in users:
        user_stocks = UserStock.objects.filter(user=u)
        if not user_stocks.exists():
            continue

        excel_file_user = create_excel_for_single_user(u, user_stocks)
        content_user = excel_file_user.read()
        user_filename = f"{u.username}_stok_{current_date_str}.xlsx"
        email.attach(
            user_filename,
            content_user,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    email.send()
    return Response({"detail": "Ana stok + kullanıcı stokları Excel maili gönderildi."}, status=200)


def test_push(request):
    """
    Sadece test fonksiyonu (push notification)
    """
    result = send_push_notification("Test Başlık", "Bu bir test push bildirimi.")
    return HttpResponse(f"Push notification result: {result}")
