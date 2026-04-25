from django.urls import path
from . import views

urlpatterns = [
    path("chat/",  views.aura_chat,  name="aura-chat"),
    path("reset/", views.aura_reset, name="aura-reset"),
]
