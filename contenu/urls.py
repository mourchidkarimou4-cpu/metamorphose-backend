from django.urls import path
from . import views

urlpatterns = [
    path('guides/',  views.guides),
    path('replays/', views.replays),
    path('newsletter/abonner/',    views.abonner_newsletter),
    path('newsletter/desabonner/', views.se_desabonner),
]
