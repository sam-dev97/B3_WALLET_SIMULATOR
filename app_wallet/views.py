from django.shortcuts import render, redirect
import yfinance as yf
from .models import StockData, PurchaseData, UserProfile
from datetime import date
from django.contrib import messages
from .forms import PurchaseForm, AdicionarSaldoForm, SellForm
from django.db import transaction
from django.contrib.auth import login, logout
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum

@login_required
def home(request):
    tickers = [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "B3SA3.SA",
        "BBAS3.SA", "ABEV3.SA", "WEGE3.SA", "MGLU3.SA", "PETR3.SA",
        "ITSA4.SA", "RENT3.SA", "LREN3.SA", "JBSS3.SA", "GGBR4.SA",
        "BTOW3.SA", "SUZB3.SA", "CSAN3.SA", "VVAR3.SA", "RAIL3.SA",
    ]

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        history = stock.history(period='1d')
        
        if not history.empty:
            latest_data = {'Close': history['Close'].iloc[-1]}
            stock_data = StockData.objects.filter(ticker=ticker, user=request.user).first()
            
            if stock_data:
                stock_data.close_price = latest_data['Close']
                stock_data.date = timezone.now().date()
                stock_data.save()
            else:
                StockData.objects.create(
                    ticker=ticker,
                    close_price=latest_data['Close'],
                    date = timezone.now().date(),
                    user=request.user,
                )
                
    remove_duplicates(request.user)

    saved_data = StockData.objects.filter(user=request.user).order_by('-date')

    if request.method == 'POST':
        
        purchase_form = PurchaseForm(request.POST)
        sell_form = SellForm(request.POST)
        
        if 'quantity_bought' in request.POST and purchase_form.is_valid():
            
            purchase_instance = purchase_form.save(commit=False)
            stock_data = StockData.objects.filter(ticker=purchase_instance.ticker, user=request.user).order_by('-date').first()
            
            if stock_data:
                purchase_instance.purchase_price = stock_data.close_price
                purchase_instance.user = request.user
                total_cost = purchase_instance.purchase_price * purchase_instance.quantity_bought
                user_profile = UserProfile.objects.get(user=request.user)
                
                if user_profile.saldo >= total_cost:
                    with transaction.atomic():
                        user_profile.saldo -= total_cost
                        user_profile.save()
                        purchase_instance.save()
                    messages.success(request, 'Purchase made successfully!')
                else:
                    messages.error(request, 'Insufficient balance to make the purchase.')
            else:
                messages.error(request, 'Ticker not found in stock data.')
                
        elif 'quantity_sell' in request.POST and sell_form.is_valid():
            ticker_sell = sell_form.cleaned_data['ticker']
            quantity_sell = sell_form.cleaned_data['quantity_sell']
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            stock_data_sell = StockData.objects.filter(ticker=ticker_sell, user=request.user).order_by('-date').first()
            
            total_bought = PurchaseData.objects.filter(ticker=ticker_sell, user=request.user).aggregate(total_bought=Sum('quantity_bought'))['total_bought'] or 0
            total_sold = PurchaseData.objects.filter(ticker=ticker_sell, user=request.user).aggregate(total_sold=Sum('quantity_sold'))['total_sold'] or 0
            net_quantity = total_bought - total_sold
            
            if net_quantity >= quantity_sell:
                stock_data_sell = StockData.objects.filter(ticker=ticker_sell, user=request.user).order_by('-date').first()
                
                if stock_data_sell and quantity_sell > 0:
                    current_price = stock_data_sell.close_price
                    total_value = current_price * quantity_sell
                    
                    if total_value > 0:
                        with transaction.atomic():
                            user_profile.saldo += total_value
                            user_profile.save()
                            
                            PurchaseData.objects.create(
                                ticker=ticker_sell,
                                quantity_sold=quantity_sell,
                                purchase_price=current_price,
                                user=request.user
                            )
                            
                        messages.success(request, f'{quantity_sell} {ticker_sell} tickets sold!')
                    else:
                        messages.error(request, 'Insufficient tickets to make the sale.')
                else:
                    messages.error(request, 'Stock data not found or invalid quantity.')
            else:
                messages.error(request, 'Insufficient tickets to make the sale.')

        return redirect('home')
    else:
        purchase_form = PurchaseForm()
        sell_form = SellForm()

    user_purchase_history = PurchaseData.objects.filter(user=request.user).order_by('-date')
    context = {
        'saved_data': saved_data,
        'purchase_form': purchase_form,
        'sell_form' : sell_form,
        'user_purchase_history': user_purchase_history,
    }

    return render(request, 'index.html', context)

def remove_duplicates(user):
    duplicates = (StockData.objects
                  .filter(user=user)
                  .values('ticker')
                  .annotate(count_id=Count('id'))
                  .filter(count_id__gt=1))
    
    for duplicate in duplicates:
        ticker = duplicate['ticker']
        dup_records = StockData.objects.filter(ticker=ticker, user=user).order_by('-date')
        for record in dup_records[1:]:
            record.delete()

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def adicionar_saldo(request):
    if request.method == 'POST':
        form = AdicionarSaldoForm(request.POST)
        if form.is_valid():
            saldo_adicionado = form.cleaned_data['saldo']
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.saldo += saldo_adicionado
            user_profile.save()
            return redirect('perfil_usuario')
    else:
        form = AdicionarSaldoForm()
    return render(request, 'adicionar_saldo.html', {'form': form})
