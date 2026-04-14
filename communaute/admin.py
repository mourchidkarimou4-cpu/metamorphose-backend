from django.contrib import admin
from .models import CleAcces, Publication, Commentaire, ProfilCommunaute

@admin.register(CleAcces)
class CleAccesAdmin(admin.ModelAdmin):
    list_display = ['utilisatrice', 'cle', 'active', 'premiere_connexion', 'creee_le']
    list_filter  = ['active']
    actions      = ['desactiver']

    def desactiver(self, request, qs):
        qs.update(active=False)
    desactiver.short_description = "Désactiver les clés sélectionnées"

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['auteure', 'contenu', 'pour_coach', 'epingle', 'visible', 'created_at']
    list_filter  = ['pour_coach', 'epingle', 'visible']

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['auteure', 'publication', 'est_coach', 'visible', 'created_at']

@admin.register(ProfilCommunaute)
class ProfilCommunauteAdmin(admin.ModelAdmin):
    list_display = ['utilisatrice', 'pays', 'secteur', 'onboarding_fait']
