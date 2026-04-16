from django.urls import path
from . import views
urlpatterns = [
    # Public
    path('',                              views.liste_cours),
    path('categories/',                   views.liste_categories),
    # Authentifié
    path('mes-cours/',                    views.mes_cours),
    # Admin CRUD cours & catégories
    path('admin/cours/',                  views.admin_cours),
    path('admin/cours/<int:pk>/',         views.admin_cours_detail),
    path('admin/categories/',             views.admin_categories),
    path('admin/categories/<int:pk>/',    views.admin_categorie_detail),
    # Admin accès
    path('admin/acces/',                  views.admin_liste_acces),
    path('admin/acces/activer/',          views.admin_activer_acces),
    path('admin/acces/desactiver/',       views.admin_desactiver_acces),
    # Webhook
    path('webhook/paiement/',             views.webhook_paiement),
    # Routes slug — EN DERNIER
    path('<slug:slug>/',                  views.detail_cours),
    path('<slug:slug>/acces/',            views.verifier_acces),
]
