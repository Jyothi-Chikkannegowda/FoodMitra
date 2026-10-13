from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('place/<int:menu_id>/', views.place_order, name='place_order'),
    path('tracking/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('cook-orders/', views.cook_orders, name='cook_orders'),
    path('update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('receipt/<int:order_id>/', views.download_receipt, name='download_receipt'),
    path('cod-confirm/', views.cod_confirm, name='cod_confirm'),
]