from django.urls import path
from . import views

urlpatterns = [
    path('creer/',                        views.creer_salle),
    path('mes-salles/',                   views.mes_salles),
    path('salles-actives/',               views.salles_actives),
    path('<str:room_id>/register-peer/',   views.register_peer),
    path('<str:room_id>/peers/',           views.list_peers),
    path('<str:room_id>/leave-peer/',      views.leave_peer),
    path('<str:room_id>/',                 views.infos_salle),
    path('<str:room_id>/rejoindre/',       views.rejoindre_salle),
    path('<str:room_id>/terminer/',        views.terminer_salle),
]
