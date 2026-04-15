from django.contrib import admin
from .models import CleAcces

@admin.register(CleAcces)
class CleAccesAdmin(admin.ModelAdmin):
    list_display  = ['email', 'cle', 'is_active', 'created_at']
    list_filter   = ['is_active']
    search_fields = ['email']
    readonly_fields = ['cle', 'created_at']
    ordering      = ['-created_at']

    fieldsets = (
        ("Identification", {
            'fields': ('email', 'cle')
        }),
        ("Statut", {
            'fields': ('is_active', 'created_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        """La clé se génère automatiquement à la création."""
        super().save_model(request, obj, form, change)

    actions = ['revoquer', 'reactiver']

    def revoquer(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} clé(s) révoquée(s).")
    revoquer.short_description = "Révoquer les clés sélectionnées"

    def reactiver(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} clé(s) réactivée(s).")
    reactiver.short_description = "Réactiver les clés sélectionnées"
