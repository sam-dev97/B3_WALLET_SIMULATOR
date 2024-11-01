from django.urls import path, include
from .views import home, custom_register, custom_login, custom_logout, transaction_history, wallet_details, ticker_info

urlpatterns = [
    path('', home, name='home'),
    path('transaction_history/', transaction_history, name='transaction_history'),
    path('wallet_details/', wallet_details, name='wallet_details'),
    path('ticker/<str:ticker>/', ticker_info, name='ticker_info'),
    
    # Parte de autenticação
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', custom_register, name='register'),
    path('logout/', custom_logout, name='logout'),
    path('login/', custom_login, name='login'),
]
