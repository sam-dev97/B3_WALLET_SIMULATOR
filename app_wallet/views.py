# Gerenciamento de views (temporáriamente)
from django.shortcuts import render, redirect
# Framework principal
import yfinance as yf
from datetime import date
# Wallet Management
from .models import StockData, UserProfile, Operation, Walletitself
# Imports de utilitáros do django
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum, Avg
from django.utils import timezone
# Lista de ações pra não poluir a view
from app_wallet import list_tickers
#Authentication
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def home(request):
    # Execução do Yfinance
    for ticker in list_tickers.tickers:
        stock = yf.Ticker(ticker)
        history = stock.history(period='1d')
        
        if not history.empty:
            latest_data = {
                'Close': history['Close'].iloc[-1] # Pega o último valor registrado
                }
            stock_data = StockData.objects.filter(ticker=ticker).first()
            
            if stock_data:
                stock_data.close_price = latest_data['Close']
                stock_data.date = timezone.now().date()
                stock_data.save()
            else:
                StockData.objects.create(
                    ticker=ticker,
                    close_price=latest_data['Close'],
                    date = timezone.now().date(),
                )
                
    saved_data = StockData.objects.all()

    if request.method == 'POST':
        operation_selected = request.POST.get('operation')
        operation_ticker = request.POST.get('ticker')
        operation_quantity = int(request.POST.get('quantity'))
        
        if operation_ticker not in list_tickers.tickers or operation_quantity < 1:
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

def update_wallet(ticker, user):
    total_bought = Operation.objects.filter(ticker=ticker, user=user, operation_type='buy').aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi comprado
    total_sold = Operation.objects.filter(ticker=ticker, user=user, operation_type='sell').aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi vendido
    net_quantity = total_bought - total_sold # Quantidade de ações disponíveis para venda
    print(total_bought, total_sold, net_quantity)
    if net_quantity >= 0:
        current_price = StockData.objects.filter(ticker=ticker).order_by('date').first().close_price # Último valor salvo
        average_price = Operation.objects.filter(ticker=ticker, user=user).aggregate(price_average=Avg('price'))['price_average'] or 0 # Valor que valem os tick
        total = average_price * net_quantity # Saldo
        
        Walletitself.objects.update_or_create(
            user=user,
            ticker=ticker,
            defaults={
                'quantity': net_quantity,
                'price': current_price,
                'price_average': average_price,
                'total' : net_quantity * current_price,
            }
        )
    else:
        Walletitself.objects.filter(user=user, ticker=ticker).delete()


# HISTÓRICO COMPLETO DE TRANSAÇÕES DE COMPRA E VENDA FEITAS
@login_required
def transaction_history(request):
    transactions = Operation.objects.filter(user=request.user).order_by('-date')
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'transaction_history.html', context)
# DETALHES DA CARTEIRA DE INVESTIMENTOS
@login_required
def wallet_details(request):
    details = Walletitself.objects.filter(user=request.user)
    context = {'details' : details}
    return render(request, 'wallet_details.html', context)
# LOGIN/LOGOUT PERSONALIZADO
def custom_register(request):
    
    if request.user.is_authenticated:
        return redirect('home')       
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2= request.POST.get('password2')
            
        #Fazer alguns testes manuais pra ver se os dados são válidos
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

@login_required
def ticker_info(request, ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    context = {
        'ticker': ticker,
        'info': info,
        'quote': {
            'previousClose': info.get('previousClose', 'N/A'),
            'open': info.get('open', 'N/A'),
            'dayLow': info.get('dayLow', 'N/A'),
            'dayHigh': info.get('dayHigh', 'N/A'),
            'volume': info.get('volume', 'N/A'),
        },
        'dividends': {
            'dividendRate': info.get('dividendRate', 'N/A'),
            'dividendYield': info.get('dividendYield', 'N/A'),
            'exDividendDate': info.get('exDividendDate', 'N/A'),
        },
    }

    return render(request, 'ticker_info.html', context)