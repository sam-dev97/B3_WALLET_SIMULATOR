from django.urls import path, include
from .views import home, custom_register, custom_login, custom_logout, TickerInfoView, TransactionHistoryView, WalletDetailsView

urlpatterns = [
    path('', home, name='home'),
    path('transaction_history/', TransactionHistoryView.as_view(), name='transaction_history'),
    path('wallet_details/', WalletDetailsView.as_view(), name='wallet_details'),
    path('ticker/<str:ticker>/', TickerInfoView.as_view(), name='ticker_info'),
    
    # Parte de autenticação
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', custom_register, name='register'),
    path('logout/', custom_logout, name='logout'),
    path('login/', custom_login, name='login'),
]
