from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('post/', views.post_menu, name='post_menu'),
    path("edit/<int:menu_id>/", views.edit_menu, name="edit_menu"),
    path("delete/<int:menu_id>/", views.delete_menu, name="delete_menu"),
    path("my-menu/", views.my_menu, name="my_menu"),
]