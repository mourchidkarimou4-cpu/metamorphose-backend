from django.urls import path
from . import views

urlpatterns = [
    path('creer/',           views.creer_reunion),
    path('signature/',       views.get_signature),
    path('liste/',           views.liste_reunions),
    path('mes-reunions/',    views.mes_reunions),
    path('<int:reunion_id>/terminer/', views.terminer_reunion),
]
