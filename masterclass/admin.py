from django.contrib import admin
from .models import Masterclass, Reservation

@admin.register(Masterclass)
class MasterclassAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'date', 'places_max', 'est_active', 'gratuite']
    list_filter   = ['est_active', 'gratuite']
    search_fields = ['titre']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = ['prenom', 'nom', 'email', 'masterclass', 'confirmee', 'created_at']
    list_filter   = ['confirmee', 'masterclass']
    search_fields = ['email', 'nom', 'prenom']
