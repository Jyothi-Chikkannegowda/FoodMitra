from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['food_name', 'cook', 'price', 'cuisine_type', 'is_veg', 'is_available']
    list_filter = ['cuisine_type', 'is_veg', 'is_available']
    search_fields = ['food_name']