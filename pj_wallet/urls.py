from django.urls import path
from app_wallet import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('adicionar_saldo/', views.adicionar_saldo, name='adicionar_saldo'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
]
