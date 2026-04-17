from django.contrib import admin
from .models import Notification, Conversation, Message, Vague, MembreVague, Progression, FormulaireSatisfaction, SessionAgenda

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['type', 'titre', 'lu', 'created_at']
    list_filter  = ['type', 'lu']

@admin.register(Vague)
class VagueAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nom', 'date_debut', 'date_fin', 'statut', 'places_prises']

@admin.register(Progression)
class ProgressionAdmin(admin.ModelAdmin):
    list_display = ['membre', 'semaine_actuelle', 'sessions_completees', 'pourcentage']

@admin.register(FormulaireSatisfaction)
class SatisfactionAdmin(admin.ModelAdmin):
    list_display = ['membre', 'note_globale', 'recommanderait', 'complete_le']

@admin.register(SessionAgenda)
class SessionAgendaAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_session', 'date_debut', 'rappel_envoye']
