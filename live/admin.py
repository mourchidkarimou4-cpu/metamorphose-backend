from django.contrib import admin
from .models import Salle, Participant, Message

@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ['titre', 'hote', 'mode', 'statut', 'created_at']
    list_filter  = ['statut', 'mode']

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['nom', 'salle', 'role', 'rejoint_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['auteur', 'salle', 'created_at']
