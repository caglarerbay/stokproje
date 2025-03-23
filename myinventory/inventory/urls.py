from django.urls import path
from rest_framework.authtoken import views as drf_auth_views
from .views import (
    register_user, login_user, forgot_password_user,
    search_product, my_stock, use_product_api, transfer_product_api,
    admin_add_product, user_list, take_product, return_product, admin_update_stock
)

urlpatterns = [
    # Auth / user management
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

    # Moved these to /api/ prefix
    path('api/take_product/<int:product_id>/', take_product, name='take_product'),
    path('api/return_product/<int:product_id>/', return_product, name='return_product'),

    # If you create the new API versions for transaction_log, critical_stock, etc.:
    # path('api/transaction_log/', transaction_log_api, name='transaction_log_api'),
    # path('api/critical_stock/', critical_stock_api, name='critical_stock_api'),
    # path('api/send_excel_report_email/', send_excel_report_email_api, name='send_excel_report_email_api'),
    # path('api/send_critical_stock_email/', send_critical_stock_email_api, name='send_critical_stock_email_api'),
]
