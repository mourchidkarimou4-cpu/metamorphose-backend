from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.liste_masterclasses),
    path('<int:pk>/reserver/',        views.reserver),
    path('admin/',                    views.admin_masterclasses),
    path('admin/<int:pk>/',           views.admin_masterclass_detail),
    path('admin/<int:pk>/reservations/', views.admin_reservations),
]
