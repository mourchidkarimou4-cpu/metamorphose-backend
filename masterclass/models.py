from django.db import models
from django.conf import settings
import cloudinary.models

class Masterclass(models.Model):
    titre       = models.CharField(max_length=200)
    description = models.TextField()
    date        = models.DateTimeField()
    image       = cloudinary.models.CloudinaryField('image', folder='metamorphose/masterclass', blank=True, null=True)
    places_max  = models.PositiveIntegerField(default=100)
    est_active  = models.BooleanField(default=True)
    gratuite    = models.BooleanField(default=True)
    lien_live   = models.URLField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        verbose_name = "Masterclass"
        verbose_name_plural = "Masterclasses"

    def __str__(self):
        return self.titre

    @property
    def places_restantes(self):
        return self.places_max - self.reservations.filter(confirmee=True).count()

    @property
    def complet(self):
        return self.places_restantes <= 0

class Reservation(models.Model):
    masterclass = models.ForeignKey(Masterclass, on_delete=models.CASCADE, related_name='reservations')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    prenom      = models.CharField(max_length=100)
    nom         = models.CharField(max_length=100)
    email       = models.EmailField()
    telephone   = models.CharField(max_length=20, blank=True)
    confirmee   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['masterclass', 'email']
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.masterclass.titre}"
