from django.urls import path
from app_wallet import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_wallet.urls')),
]
