from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order, Payment

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'cook', 'menu_item', 'quantity', 'total_price', 'status', 'delivery_type', 'order_time']
    list_filter = ['status', 'delivery_type']
    search_fields = ['customer__username', 'menu_item__food_name']
    ordering = ['-order_time']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'payment_method', 'status', 'transaction_id']
    list_filter = ['status', 'payment_method']
    ordering = ['-id']