# paiement/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('initier/',              views.initier_paiement),
    path('webhook/',              views.webhook_fedapay),
    path('statut/<int:tid>/',     views.statut_paiement),
]
