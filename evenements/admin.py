from django.contrib import admin
from .models import Evenement, Actualite

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'date', 'statut', 'actif', 'ordre']
    list_filter  = ['statut', 'actif']

@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'date', 'actif', 'ordre']
    list_filter  = ['actif']
