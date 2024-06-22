# forms.py
from django import forms
from .models import PurchaseData
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = PurchaseData
        fields = ['ticker', 'quantity_bought']
        
        widgets = {
            'ticker' : forms.TextInput(attrs={
                'class' : 'form-control custom-ticker'
            }),
            'quantity_bought' : forms.NumberInput(attrs={
                'class' : 'form-control custom-quantity'
            }),
        }
        
        labels = {
            'ticker': 'Código da Ação',
            'quantity_bought': 'Quantidade',
        }

class SellForm(forms.Form):
    ticker = forms.CharField(label='Código da Ação', max_length=10, widget=forms.TextInput(attrs={'class': 'form-control custom-ticker'}))
    quantity_sell = forms.IntegerField(label = 'Quantidade', min_value=1,  widget=forms.TextInput(attrs={'class': 'form-control custom-quantity'}))
    
    
    
    
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
class AdicionarSaldoForm(forms.Form):
    saldo = forms.DecimalField(label='Adicionar saldo', max_digits=10, decimal_places=2)