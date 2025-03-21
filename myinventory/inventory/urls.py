from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import register_user
from .views import login_user
from .views import forgot_password_user

urlpatterns = [
    path('', views.index, name='index'),
    path('api/register/', register_user, name='register_user'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='inventory/password_change.html'),
         name='password_change'),
    path('password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='inventory/password_change_done.html'),
         name='password_change_done'),

    path('add_product/', views.add_product, name='add_product'),
    path('take_product/<int:product_id>/', views.take_product, name='take_product'),
    path('return_product/<int:product_id>/', views.return_product, name='return_product'),
    path('transfer_product/<int:product_id>/', views.transfer_product, name='transfer_product'),
    path('use_product/<int:product_id>/', views.use_product, name='use_product'),

    path('transaction_log/', views.transaction_log, name='transaction_log'),
    path('critical_stock/', views.critical_stock_list, name='critical_stock_list'),
    path('send_excel_report/', views.send_excel_report_email, name='send_excel_report'),

     path('api/login/', login_user, name='login_user'),
     
     path('api/forgot_password/', forgot_password_user, name='forgot_password_user')
    
]
