from django.urls import path
from . import views

urlpatterns = [
    path('creneaux/',           views.creneaux_disponibles),
    path('reserver/',           views.prendre_rdv),
    path('admin/liste/',        views.admin_liste_rdv),
    path('admin/<int:pk>/',     views.admin_action_rdv),
    path('admin/disponibilites/',        views.admin_disponibilites),
    path('admin/disponibilites/<int:pk>/', views.admin_disponibilite_detail),
]
