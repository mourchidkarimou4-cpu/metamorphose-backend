from django.urls import path
from . import views

urlpatterns = [
    path('initier/',   views.initier_paiement),
    path('confirmer/', views.confirmer_paiement),
    path('webhook/',   views.webhook_kkiapay),
]
