from django.db import models
from django.conf import settings
import cloudinary.models

class DemandeContact(models.Model):
    prenom   = models.CharField(max_length=60)
    nom      = models.CharField(max_length=60)
    email    = models.EmailField()
    whatsapp = models.CharField(max_length=20)
    pays     = models.CharField(max_length=60)
    formule  = models.CharField(max_length=10)
    message  = models.TextField(blank=True)
    date     = models.DateTimeField(auto_now_add=True)
    traite   = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.formule}"

class Guide(models.Model):
    titre   = models.CharField(max_length=200)
    fichier = cloudinary.models.CloudinaryField(
        'raw', resource_type='raw',
        folder='metamorphose/guides',
        blank=True, null=True
    )
    numero  = models.IntegerField()
    actif   = models.BooleanField(default=True)

    def __str__(self):
        return f"Bonus {self.numero} — {self.titre}"

class Replay(models.Model):
    titre    = models.CharField(max_length=200)
    video_url= models.URLField()
    semaine  = models.IntegerField()
    formules = models.CharField(max_length=20, default='F1,F2,F3,F4')
    actif    = models.BooleanField(default=True)
    code_acces = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"S{self.semaine} — {self.titre}"


class Abonne(models.Model):
    email      = models.EmailField(unique=True)
    prenom     = models.CharField(max_length=60, blank=True)
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Abonné newsletter'
        verbose_name_plural = 'Abonnés newsletter'

    def __str__(self):
        return f"{self.email} — {'actif' if self.actif else 'désabonné'}"
