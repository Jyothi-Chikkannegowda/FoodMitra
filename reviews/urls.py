from django.urls import path
from . import views

urlpatterns = [
    path('', views.review_list, name='review_list'),
    path('add/<int:order_id>/', views.add_review, name='add_review'),
]