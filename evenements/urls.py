from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.liste_evenements),
    path('admin/',                  views.admin_evenements),
    path('admin/<int:pk>/',         views.admin_evenement_detail),
    path('actualites/',             views.liste_actualites),
    path('actualites/admin/',       views.admin_actualites),
    path('actualites/admin/<int:pk>/', views.admin_actualite_detail),
]
