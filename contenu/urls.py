from django.urls import path
from . import views

urlpatterns = [
    path('guides/',  views.guides),
    path('replays/', views.replays),
    path('newsletter/abonner/',    views.abonner_newsletter),
    path('newsletter/desabonner/', views.se_desabonner),
    path('replays/<int:replay_id>/',       views.infos_replay_public),
    path('replays/<int:replay_id>/acces/', views.acceder_replay),
]
