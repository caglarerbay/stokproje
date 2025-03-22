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






@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    JSON bekliyoruz:
    {
      "username": "ali",
      "password": "ali12345"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"detail": "Kullanıcı adı ve şifre zorunludur."},
                        status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)  # Django session oluşturur
        return Response({"detail": "Giriş başarılı."}, status=status.HTTP_200_OK)
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
@permission_classes([AllowAny])
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



@staff_member_required
def critical_stock_list(request):
    # Kritik stok: ürün miktarı min_limit'in altındaysa (sipariş durumu farketmeksizin)
    critical_products = Product.objects.filter(quantity__lt=F('min_limit'))
    return render(request, "inventory/critical_stock_list.html", {"critical_products": critical_products})






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
@api_view(['POST'])
@permission_classes([AllowAny])
def take_product(request, product_id):
    """
    JSON tabanlı alma işlemi:
    POST /take_product/<product_id>/
    Body: { "quantity": 3 }

    Bu fonksiyon, ana depodan car stoğuna ürün alır.
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    # Ana stokta yeterli var mı
    if product.quantity < qty:
        return Response({"detail": "Ana stokta yeterli miktar yok."}, status=status.HTTP_400_BAD_REQUEST)

    # Kullanıcının stoğunu bul veya oluştur
    user = request.user if request.user.is_authenticated else None
    # Not: eğer 'AllowAny' kullanıyorsan, user anonymous olabilir. Geliştirme aşamasında test için.
    # Üretimde "IsAuthenticated" yapmak daha mantıklı.
    if not user:
        return Response({"detail": "Kullanıcı doğrulanmadı."}, status=status.HTTP_401_UNAUTHORIZED)

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
@permission_classes([AllowAny])
def return_product(request, product_id):
    """
    JSON tabanlı iade işlemi:
    POST /return_product/<product_id>/
    Body: { "quantity": 2 }

    Bu fonksiyon, car stoğundan ana stoğa ürün iade eder.
    """
    product = get_object_or_404(Product, id=product_id)
    data = request.data
    qty = data.get('quantity', 0)

    try:
        qty = int(qty)
    except ValueError:
        return Response({"detail": "Geçersiz quantity"}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user if request.user.is_authenticated else None
    if not user:
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



@login_required
@login_required
def transfer_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    sender_stock = get_object_or_404(UserStock, user=request.user, product=product)

    if request.method == "POST":
        form = TransferProductForm(request.POST)
        if form.is_valid():
            target_username = form.cleaned_data['target_username']
            qty = form.cleaned_data['quantity']

            if sender_stock.quantity < qty:
                form.add_error('quantity', 'Kişisel stokta yeterli miktar yok.')
                return render(request, 'inventory/transfer_product.html', {
                    'form': form,
                    'product': product,
                    'sender_stock': sender_stock
                })

            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                form.add_error('target_username', 'Belirtilen kullanıcı bulunamadı.')
                return render(request, 'inventory/transfer_product.html', {
                    'form': form,
                    'product': product,
                    'sender_stock': sender_stock
                })

            receiver_stock, created = UserStock.objects.get_or_create(user=target_user, product=product)

            sender_stock.quantity -= qty
            sender_stock.save()

            receiver_stock.quantity += qty
            receiver_stock.save()

            StockTransaction.objects.create(
                product=product,
                transaction_type="TRANSFER",
                quantity=qty,
                user=request.user,
                target_user=target_user,
                description="Kullanıcılar arası transfer yapıldı.",
                current_user_quantity=sender_stock.quantity,
                current_receiver_quantity=receiver_stock.quantity
            )

            return redirect('index')
    else:
        form = TransferProductForm()

    return render(request, 'inventory/transfer_product.html', {
        'form': form,
        'product': product,
        'sender_stock': sender_stock
    })


@login_required
def use_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_stock = get_object_or_404(UserStock, user=request.user, product=product)

    if request.method == "POST":
        form = UseProductForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data['quantity']
            if user_stock.quantity < qty:
                form.add_error('quantity', 'Kişisel stokta yeterli miktar yok.')
                return render(request, 'inventory/use_product.html', {
                    'form': form,
                    'product': product,
                    'user_stock': user_stock
                })

            user_stock.quantity -= qty
            user_stock.save()

            StockTransaction.objects.create(
                product=product,
                transaction_type="USE",
                quantity=qty,
                user=request.user,
                description="Kullanıcı ürünü kullandı.",
                current_user_quantity=user_stock.quantity
            )

            return redirect('index')
    else:
        form = UseProductForm(initial={'product_id': product.id})

    return render(request, 'inventory/use_product.html', {
        'form': form,
        'product': product,
        'user_stock': user_stock
    })


@staff_member_required
def transaction_log(request):
    logs = StockTransaction.objects.all().order_by('-timestamp')
    return render(request, 'inventory/transaction_log.html', {'logs': logs})


@staff_member_required
def send_critical_stock_email(request):
    from django.db.models import F
    critical_products = Product.objects.filter(quantity__lt=F('min_limit'))

    # Siparişi çekilmemiş ve çekilmiş ürünleri ayıralım:
    not_ordered = critical_products.filter(order_placed=False)
    ordered = critical_products.filter(order_placed=True)

    subject = "Kritik Stok Uyarısı"
    message = "Kritik Stok Durumu Uyarısı:\n\n"

    # Siparişi Çekilmemiş Ürünler:
    message += "Siparişi Çekilmemiş Ürünler:\n"
    if not_ordered.exists():
        header = f"{'Parça Kodu':<12} {'Ürün İsmi':<20} {'Mevcut Adet':>12} {'Min Limit':>10}\n"
        divider = "-" * 60 + "\n"
        message += divider + header + divider
        for product in not_ordered:
            message += f"{product.part_code:<12} {product.name:<20} {product.quantity:>12} {product.min_limit:>10}\n"
        message += divider + "\n"
    else:
        message += "Bu kategori için kritik stok ürünü bulunmamaktadır.\n\n"

    # Siparişi Çekilmiş Ürünler:
    message += "Siparişi Çekilmiş Ürünler, Tedariği Bekleniyor:\n"
    if ordered.exists():
        header = f"{'Parça Kodu':<12} {'Ürün İsmi':<20} {'Mevcut Adet':>12} {'Min Limit':>10}\n"
        divider = "-" * 60 + "\n"
        message += divider + header + divider
        for product in ordered:
            message += f"{product.part_code:<12} {product.name:<20} {product.quantity:>12} {product.min_limit:>10}\n"
        message += divider + "\n"
    else:
        message += "Bu kategori için kritik stok ürünü bulunmamaktadır.\n\n"

    recipient = settings.CRITICAL_STOCK_ALERT_RECIPIENT
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])

    # Mail gönderildikten sonra, sipariş çekilmemiş ürünleri sipariş çekilmiş olarak işaretleyelim.
    not_ordered.update(order_placed=True)

    messages.success(request, "Kritik stok uyarı maili gönderildi.")
    return redirect('critical_stock_list')


@staff_member_required
def send_excel_report_email(request):
    from django.db.models import F
    critical_products = Product.objects.filter(quantity__lt=F('min_limit'))
    if not critical_products.exists():
        messages.info(request, "Kritik stok ürünü bulunamadı. Mail gönderilmeyecek.")
        return redirect('critical_stock_list')

    excel_file = create_excel_report(critical_products)
    excel_content = excel_file.read()
    excel_file.seek(0)

    subject = "Kritik Stok Excel Raporu"
    body = "Ek'te, kritik stok raporunu bulabilirsiniz."
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.CRITICAL_STOCK_ALERT_RECIPIENT])
    email.attach('kritik_stok_raporu.xlsx', excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()

    # Push bildirim gönderelim: Kritik stok uyarısı.
    notification_title = "Kritik Stok Uyarısı"
    notification_body = "Bazı ürünlerin stokları kritik seviyeye düştü. Lütfen kontrol ediniz."
    send_push_notification(notification_title, notification_body)

    messages.success(request, "Kritik stok Excel raporlu e-posta ve push bildirim gönderildi.")
    return redirect('critical_stock_list')




#push test fonsksiyonu silinecek
from django.http import HttpResponse
from .reports import send_push_notification
def test_push(request):
    result = send_push_notification("Test Başlık", "Bu bir test push bildirimi.")
    return HttpResponse(f"Push notification result: {result}")
