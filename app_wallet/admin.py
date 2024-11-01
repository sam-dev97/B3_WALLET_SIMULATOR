from django.contrib import admin
from .models import UserProfile, StockData, Walletitself, Operation

# Customização da exibição do UserProfile no admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'saldo')
    search_fields = ('user__username',)
    list_filter = ('saldo',)

# Customização da exibição do StockData no admin
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'close_price', 'date')
    list_filter = ('ticker', 'date')

# Customização da exibição do Walletitself no admin
class WalletitselfAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticker', 'quantity', 'price', 'price_average', 'total')
    search_fields = ('user__username', 'ticker')
    list_filter = ('ticker',)
    
class OperationAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticker', 'quantity', 'price', 'balance_before', 'balance_after', 'operation_type', 'date' )
    search_fields = ('user__username', 'ticker')
    list_filter = ('ticker', 'user')
    
# Registrar todos os modelos no admin
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(StockData, StockDataAdmin)
admin.site.register(Walletitself, WalletitselfAdmin)
admin.site.register(Operation, OperationAdmin)