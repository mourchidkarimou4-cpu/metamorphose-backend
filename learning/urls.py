from django.urls import path
from . import views

urlpatterns = [
    path('categories/',           views.categories_list),
    path('cours/',                views.cours_list),
    path('cours/<slug:slug>/',    views.cours_detail),
    path('admin/cours/',          views.admin_cours_list),
    path('admin/cours/<int:pk>/', views.admin_cours_detail),
    path('admin/categories/',     views.admin_categories_list),
]
