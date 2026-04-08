from django.contrib import admin
from .models import Categorie, Cours

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug', 'icone', 'ordre']
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'format', 'niveau', 'semaine', 'actif', 'en_vedette']
    list_filter  = ['format', 'niveau', 'actif', 'en_vedette', 'categorie']
    prepopulated_fields = {'slug': ('titre',)}
