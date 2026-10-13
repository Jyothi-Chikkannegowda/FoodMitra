from django.contrib import admin
from .models import CookProfile, CustomerProfile

@admin.register(CookProfile)
class CookProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'speciality', 'is_verified', 'rating', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['user__username', 'speciality']
    list_editable = ['is_verified']

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username']