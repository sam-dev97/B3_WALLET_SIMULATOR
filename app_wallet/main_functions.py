import yfinance as yf
from datetime import date
from django.utils import timezone
from .models import StockData, UserProfile, Operation, Walletitself
from django.db.models import Count, Sum, Avg
tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "B3SA3.SA", "AAPL", "GOOGL", "MSFT", "JBSS3.SA", "COGN3.SA"]

def get_ticker_info():
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        history = stock.history(period='1d')
        
        if not history.empty:
            latest_data = {
                'Close': history['Close'].iloc[-1]
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
def update_wallet(ticker, user):
    total_bought = Operation.objects.filter(ticker=ticker, user=user, operation_type='buy').aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi comprado
    total_sold = Operation.objects.filter(ticker=ticker, user=user, operation_type='sell').aggregate(Sum('quantity'))['quantity__sum'] or 0 # Soma de tudo que já foi vendido
    net_quantity = total_bought - total_sold # Quantidade de ações disponíveis para venda
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
    return context