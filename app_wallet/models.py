from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00)
    
    def __str__(self):
        return self.user.username

# Sempre que um usuário é criado, ao mesmo tempo é criado um perfil para ess usuário
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
# Sempre salva o perfil quando alguma alteração é feita no usuário
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
    
class StockData(models.Model):
    ticker = models.CharField(max_length=10)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True) 

    def __str__(self):
        return f"{self.ticker} - {self.date}"
    
class Operation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    operation_type = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateTimeField(auto_now_add=True)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user} - {self.ticker} - {self.operation_type} - {self.date}"
    
    
class Walletitself(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_average = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user} - {self.ticker}"

class BugReport(models.Model):
    bug_title = models.CharField(max_length=200)
    bug_description = models.TextField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)