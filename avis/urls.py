from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                          views.liste_publique),
    # Membre
    path('soumettre/',                views.soumettre),
    path('mes-temoignages/',          views.mes_temoignages),
    # Admin
    path('admin/',                    views.liste_admin),
    path('admin/ajouter/',            views.ajouter),
    path('admin/<int:pk>/',           views.modifier),
    path('admin/<int:pk>/modifier/',  views.modifier_complet),
    path('admin/<int:pk>/approuver/', views.approuver),
    path('admin/<int:pk>/refuser/',   views.refuser),
    path('admin/<int:pk>/supprimer/', views.supprimer),
]
