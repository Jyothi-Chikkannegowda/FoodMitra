from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/dashboard/', views.dashboard, name='dashboard'),
    path('accounts/admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('accounts/verify-cook/<int:cook_id>/', views.verify_cook, name='verify_cook'),
    path('accounts/earnings/', views.earnings, name='earnings'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/update-profile/', views.update_profile, name='update_profile'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('accounts/toggle-availability/', views.toggle_availability, name='toggle_availability'),
]