from django.db import models
import cloudinary.models

class Evenement(models.Model):
    STATUT = [('a_venir','À venir'),('en_cours','En cours'),('termine','Terminé')]
    titre       = models.CharField(max_length=200)
    badge       = models.CharField(max_length=50, blank=True)
    badge_color = models.CharField(max_length=20, default='#C9A96A')
    date        = models.CharField(max_length=100)
    lieu        = models.CharField(max_length=200)
    description = models.TextField()
    bouton      = models.CharField(max_length=100, blank=True)
    lien        = models.CharField(max_length=200, blank=True)
    photo       = cloudinary.models.CloudinaryField('image', folder='metamorphose/evenements', blank=True, null=True)
    photo_url   = models.URLField(max_length=500, blank=True, default='')
    statut      = models.CharField(max_length=20, choices=STATUT, default='a_venir')
    ordre       = models.IntegerField(default=0)
    actif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return self.titre

class Actualite(models.Model):
    titre      = models.CharField(max_length=200)
    categorie  = models.CharField(max_length=50)
    date       = models.CharField(max_length=50)
    resume     = models.TextField()
    bouton     = models.CharField(max_length=100, blank=True)
    lien       = models.CharField(max_length=200, blank=True)
    photo      = cloudinary.models.CloudinaryField('image', folder='metamorphose/actualites', blank=True, null=True)
    photo_url  = models.URLField(max_length=500, blank=True, default='')
    color      = models.CharField(max_length=20, default='#C9A96A')
    ordre      = models.IntegerField(default=0)
    actif      = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return self.titre
