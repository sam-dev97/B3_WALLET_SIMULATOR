from django.urls import path, include
from .views import HomeIndexView, UserRegisterView, custom_logout, TickerInfoView, TransactionHistoryView, WalletDetailsView, UserLoginView

urlpatterns = [
    path('', HomeIndexView.as_view(), name='home'),
    path('transaction_history/', TransactionHistoryView.as_view(), name='transaction_history'),
    path('wallet_details/', WalletDetailsView.as_view(), name='wallet_details'),
    path('ticker/<str:ticker>/', TickerInfoView.as_view(), name='ticker_info'),
    
    # Parte de autenticação
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
]
