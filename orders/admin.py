from django.contrib import admin
from .models import Restaurant, MenuItem, Order, Payment

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'phone')
    search_fields = ('name', 'location')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'restaurant', 'price', 'image')
    list_filter = ('restaurant',)
    search_fields = ('name', 'restaurant__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'restaurant', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'restaurant')
    search_fields = ('user__username', 'restaurant__name')
    filter_horizontal = ('items',)  # nice multi-select for many-to-many items

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('order__id', 'transaction_id')
