from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                          views.liste_cours),
    path('categories/',               views.liste_categories),
    path('<slug:slug>/',              views.detail_cours),

    # Authentifié
    path('mes-cours/',                views.mes_cours),
    path('<slug:slug>/acces/',        views.verifier_acces),

    # Admin — Coach AHONON
    path('admin/acces/',              views.admin_liste_acces),
    path('admin/acces/activer/',      views.admin_activer_acces),
    path('admin/acces/desactiver/',   views.admin_desactiver_acces),

    # Webhook paiement externe
    path('webhook/paiement/',         views.webhook_paiement),
]
