from django.db import models
from django.utils.crypto import get_random_string

class CleAcces(models.Model):
    """
    Clé d'accès à la Communauté MMO.
    Générée par Coach Prélia APEDO AHONON pour chaque Métamorphosée ayant terminé le programme.
    """
    email      = models.EmailField(unique=True, verbose_name="Email de la Métamorphosée")
    cle        = models.CharField(max_length=12, unique=True, verbose_name="Clé d'accès")
    is_active  = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Clé d'accès Communauté"
        verbose_name_plural = "Clés d'accès Communauté"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} — {self.cle} ({'Active' if self.is_active else 'Révoquée'})"

    def save(self, *args, **kwargs):
        # Génération automatique de la clé si absente
        if not self.cle:
            self.cle = self._generer_cle_unique()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_cle_unique():
        while True:
            cle = get_random_string(10, 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
            if not CleAcces.objects.filter(cle=cle).exists():
                return cle
