from django.urls import path
from . import views

urlpatterns = [
    path('creer/',                views.creer_salle),
    path('<str:room_id>/',        views.infos_salle),
    path('<str:room_id>/rejoindre/', views.rejoindre_salle),
    path('<str:room_id>/terminer/',  views.terminer_salle),
    path('mes-salles/',           views.mes_salles),
]
