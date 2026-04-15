from django.contrib import admin
from django.utils.html import format_html
from .models import Categorie, Cours, AccesCours

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'slug', 'ordre']
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'categorie', 'format', 'niveau', 'actif', 'en_vedette', 'ordre']
    list_filter   = ['actif', 'en_vedette', 'format', 'niveau', 'categorie']
    search_fields = ['titre', 'description']
    prepopulated_fields = {'slug': ('titre',)}

@admin.register(AccesCours)
class AccesCoursAdmin(admin.ModelAdmin):
    list_display   = ['user_email', 'cours', 'source', 'actif', 'created_at', 'toggle_acces']
    list_filter    = ['actif', 'source', 'cours']
    search_fields  = ['user__email', 'cours__titre']
    readonly_fields = ['created_at']
    actions        = ['activer_acces', 'desactiver_acces']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email utilisatrice"

    def toggle_acces(self, obj):
        if obj.actif:
            url = f"/admin/learning/acces-cours/{obj.pk}/desactiver/"
            return format_html('<a href="{}" style="color:red">Desactiver</a>', url)
        else:
            url = f"/admin/learning/acces-cours/{obj.pk}/activer/"
            return format_html('<a href="{}" style="color:green">Activer</a>', url)
    toggle_acces.short_description = "Action rapide"

    def activer_acces(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} acces actives par Coach Prélia APEDO AHONON.")
    activer_acces.short_description = "Activer les acces selectionnes"

    def desactiver_acces(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} acces desactives.")
    desactiver_acces.short_description = "Desactiver les acces selectionnes"
