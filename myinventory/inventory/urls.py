from django.urls import path
from rest_framework.authtoken import views as drf_auth_views
from django.http import HttpResponse
from django.contrib import admin
from .views import (
    register_user, login_user, forgot_password_user,
    search_product, my_stock, use_product_api, transfer_product_api,
    admin_add_product, user_list, take_product, return_product, admin_update_stock,admin_adjust_user_stock, 
     admin_list_user_stocks, transaction_log_api, critical_stock_api, send_excel_report_email_api, 
     admin_update_min_limit, admin_update_app_settings, send_full_stock_report_api, admin_get_app_settings, admin_generate_daily_code, 
     direct_transfer_product
)


def home(request):
    return HttpResponse("Hoş geldiniz, Django backend çalışıyor!")


urlpatterns = [
    # Auth / user management
    path('', home, name='home'),  # Root URL için basit bir view
    
    path('api/register/', register_user, name='register_user'),
    path('api/login/', login_user, name='login_user'),
    path('api/forgot_password/', forgot_password_user, name='forgot_password_user'),
    path('api-token-auth/', drf_auth_views.obtain_auth_token),

    # Product / stock endpoints
    path('api/search_product/', search_product, name='search_product'),
    path('api/my_stock/', my_stock, name='my_stock'),
    path('api/use_product/<int:product_id>/', use_product_api, name='use_product_api'),
    path('api/transfer_product/<int:product_id>/', transfer_product_api, name='transfer_product_api'),
    path('api/admin_add_product/', admin_add_product, name='admin_add_product'),
    path('api/admin_update_stock/<int:product_id>/', admin_update_stock, name='admin_update_stock'),
    path('api/user_list/', user_list, name='user_list'),
    path('api/admin_list_user_stocks/', admin_list_user_stocks, name='admin_list_user_stocks'),
    path('api/admin_adjust_user_stock/', admin_adjust_user_stock, name='admin_adjust_user_stock'),
    path('api/transaction_log_api/', transaction_log_api, name='transaction_log_api'),
    path('api/critical_stock_api/', critical_stock_api, name='critical_stock_api'),
    path('api/send_excel_report_email_api/', send_excel_report_email_api, name='send_excel_report_email_api'),
     path('api/admin_update_min_limit/<int:product_id>/', admin_update_min_limit, name='admin_update_min_limit'),
    # Moved these to /api/ prefix
    path('api/take_product/<int:product_id>/', take_product, name='take_product'),
    path('api/return_product/<int:product_id>/', return_product, name='return_product'),
    path('api/admin_update_app_settings/', admin_update_app_settings, name='admin_update_app_settings'),
    path('api/send_full_stock_report/', send_full_stock_report_api, name='send_full_stock_report_api'),
    path('api/admin_get_app_settings/', admin_get_app_settings, name='admin_get_app_settings'),
     path('api/admin_generate_daily_code/', admin_generate_daily_code, name='admin_generate_daily_code'),
     path('api/direct_transfer_product/<int:product_id>/', direct_transfer_product, name='direct_transfer_product'),
    # If you create the new API versions for transaction_log, critical_stock, etc.:
    
    
    
    
]
