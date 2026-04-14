from django.urls import path
from . import views

urlpatterns = [
    path('valider-cle/',              views.valider_cle),
    path('verifier-acces/',           views.verifier_acces),
    path('publications/',             views.publications),
    path('publications/<str:pk>/supprimer/', views.supprimer_publication),
    path('publications/<str:pk>/epingler/',  views.epingler_publication),
    path('publications/<str:pub_id>/commentaires/', views.commentaires),
    path('commentaires/<str:pk>/supprimer/', views.supprimer_commentaire),
    path('profil/',                   views.profil_communaute),
    path('admin/cles/',               views.liste_cles),
    path('admin/cles/generer/',       views.generer_cle),
    path('admin/cles/<int:pk>/toggle/', views.toggle_cle),
]
