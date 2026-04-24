from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',        views.register),
    path('login/',           views.login),
    path('me/',              views.me),
    path('refresh/',         TokenRefreshView.as_view()),
    path('contact/',         views.contact),
    path('confirmer-paiement/', views.confirmer_paiement),
    path('confirmer-don/', views.confirmer_don),
    path('confirmer-brunch/', views.confirmer_brunch),
    path('reserver-brunch/',  views.reserver_brunch),
    path('valider-brunch/',   views.valider_paiement_brunch),
    path('verifier-brunch/',  views.verifier_token_brunch),
    path('update-profile/',  views.update_profile),
    path('change-password/', views.change_password),
    path('reset-password/',  views.demander_reset),
    path('reset-confirm/',   views.confirmer_reset),
    path('certificat/',      views.generer_certificat),
]
