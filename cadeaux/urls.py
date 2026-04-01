from django.urls import path
from . import views

urlpatterns = [
    path('commander/',          views.commander_carte),
    path('verifier/<str:code>/',views.verifier_carte),
    path('admin/liste/',        views.liste_cartes),
    path('admin/<int:pk>/',     views.modifier_carte),
    path('admin/<int:pk>/activer/', views.activer_carte),
    path('admin/<int:pk>/utiliser/',views.utiliser_carte),
]
