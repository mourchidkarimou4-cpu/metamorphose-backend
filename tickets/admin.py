from django.contrib import admin
from .models import Evenement, Ticket

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'date', 'lieu', 'places_total', 'places_restantes', 'prix', 'actif']
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'evenement', 'statut', 'email', 'created_at']
    list_filter  = ['statut', 'evenement']
