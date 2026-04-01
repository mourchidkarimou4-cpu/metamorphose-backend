from django.urls import path
from . import views

urlpatterns = [
    path('guides/',  views.guides),
    path('replays/', views.replays),
]
