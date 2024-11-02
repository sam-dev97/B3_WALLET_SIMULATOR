#Funções principais do sistema
from .main_functions import get_ticker_info, tickers, update_wallet, ticker_info

# Gerenciamento de views (temporáriamente)
from django.shortcuts import render, redirect
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# Wallet Management
from .models import StockData, UserProfile, Operation, Walletitself

# Imports de utilitáros do django
from django.db import transaction
from django.db.models import Count, Sum, Avg

#Authentication
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def home(request):
    get_ticker_info()
        
    saved_data = StockData.objects.all()

    if request.method == 'POST':
        operation_selected = request.POST.get('operation')
        operation_ticker = request.POST.get('ticker')
        operation_quantity = int(request.POST.get('quantity'))
        
        if operation_ticker not in tickers or operation_quantity < 1:
            messages.warning(request, "Ticker doesn't exist or invalid quantity!")
        else:
            user_profile = UserProfile.objects.get(user=request.user)
        
            if operation_selected == 'buy':
                
                # Seleciona do modelo stock_data o ticker que foi enviado no formulário, seleciona por data o mais recente
                stock_data = StockData.objects.filter(ticker=operation_ticker).order_by('-date').first()
                
                if stock_data:
                    purchase_price = stock_data.close_price # Envia cria uma variável com o preço do ticker recuperado no banco de dados
                    user = request.user # Cria a variável temporária do usuário para a instancia
                    total_cost = purchase_price * operation_quantity # Calcula o preço total da compra
                    
                    if user_profile.saldo >= total_cost:
                        with transaction.atomic(): # Garantia de consistência dos dados
                            balance_before = user_profile.saldo # Segurando o valor do saldo atual
                            user_profile.saldo -= total_cost # Reduzindo o valor debitado da compra
                            user_profile.save() # Salvando no user profile o valor novo do saldo pós compra
                            
                            Operation.objects.create( # Salvando no modelo "Operation" os novos valores
                                user=request.user, 
                                ticker=operation_ticker, 
                                quantity=operation_quantity, 
                                operation_type='buy', 
                                price=purchase_price, 
                                balance_before=balance_before, 
                                balance_after=user_profile.saldo 
                            )       
                            update_wallet(operation_ticker, request.user) # Chamando a função de atualização da carteira PESSOAL passando os dados salvos na instância
                        messages.success(request, 'Purchase made successfully!')
                    else:
                        messages.warning(request, 'Insufficient balance to make the purchase.')
                else:
                    messages.warning(request, 'Ticker not found in stock data.')
                    
            elif operation_selected == 'sell':
                ticker_sell = operation_ticker # Ticker a ser vendido
                quantity = operation_quantity # Quantidade a ser vendida
                stock_data_sell = StockData.objects.filter(ticker=ticker_sell).order_by('-date').first() # Recupera a ação com o último registro de valor salvo
                
                total_bought = Operation.objects.filter(ticker=ticker_sell, user=request.user, operation_type='buy').aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi comprado
                total_sold = Operation.objects.filter(ticker=ticker_sell, user=request.user, operation_type=operation_selected).aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi vendido
                net_quantity = total_bought - total_sold # Quantidade de ações disponíveis para venda
                
                if net_quantity >= quantity:
                    if stock_data_sell and quantity > 0:
                        current_price = stock_data_sell.close_price # Define o valor atual como o valor recuperado pelo yFinance e salvo no Stockdata
                        total_value = current_price * quantity # Multiplica o preço atual pela quantidade a ser vendida
                        
                        if total_value > 0:
                            with transaction.atomic(): # Integridade
                                balance_before=user_profile.saldo # Recupera valor atual de saldo
                                user_profile.saldo += total_value # Atualiza o saldo com a adição dos valores advindos da venda
                                user_profile.save() # Salva o perfil do usuário
                                
                                Operation.objects.create(
                                    user=request.user,
                                    ticker=ticker_sell,
                                    quantity=quantity,
                                    operation_type='sell',
                                    price=current_price,
                                    balance_before=balance_before,
                                    balance_after=user_profile.saldo
                                )                             
                                update_wallet(ticker_sell, request.user)
                            messages.success(request, f'{quantity} {ticker_sell} tickets sold!')
                        else:
                            messages.warning(request, 'Insufficient tickets to make the sale.')
                    else:
                        messages.warning(request, 'Stock data not found or invalid quantity.')
                else:
                    messages.warning(request, 'Insufficient tickets to make the sale.')
            return redirect('home')

    user_purchase_history = Operation.objects.filter(user=request.user, operation_type='buy').order_by('-date')[:5]
    user_sales_history = Operation.objects.filter(user=request.user, operation_type='sell').order_by('-date')[:5]
    
    context = {
        'saved_data' : saved_data,
        'user_purchase_history': user_purchase_history,
        'user_sales_history': user_sales_history,
    }

    return render(request, 'index.html', context)


class TransactionHistoryView(LoginRequiredMixin, ListView):
    model = Operation
    template_name = 'transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 10

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user).order_by('-date')

class WalletDetailsView(LoginRequiredMixin, ListView):
    model = Walletitself
    template_name = 'wallet_details.html'
    context_object_name = 'details'

    def get_queryset(self):
        return Walletitself.objects.filter(user=self.request.user).order_by('-price')

def custom_register(request):
    
    if request.user.is_authenticated:
        return redirect('home')       
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2= request.POST.get('password2')
        
        if username and email and password:
            if User.objects.filter(username=username).exists():
                messages.warning(request,"This username already exists!")
            elif User.objects.filter(email=email).exists():
                messages.warning(request,"This e-mail already in use!")
            elif password != password2:
                messages.warning(request,'The passwords are diferent!.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user = authenticate(request, username=username, password=password)
                login(request, user)
                return redirect('home')
        else:
            messages.alert(request, "Please fill all the fields")
                
    return render(request, 'registration/register.html')

        
def custom_logout(request):
    logout(request)
    return redirect('login')

def custom_login(request):
    
    if request.user.is_authenticated:
        return redirect('home')    
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            if User.objects.filter(username=username).exists():
                messages.warning(request, 'Wrong password!')
            else:
                messages.error(request, "User not registered")
                return render(request, 'registration/login.html')
            
    return render(request, 'registration/login.html')

class TickerInfoView(LoginRequiredMixin, TemplateView):
    template_name = 'ticker_info.html'