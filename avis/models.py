from django.db import models
from django.conf import settings

class Temoignage(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('approuve',   'Approuvé'),
        ('refuse',     'Refusé'),
    ]
    NOTES = [(i, f'{i} étoile{"s" if i>1 else ""}') for i in range(1, 6)]
    TYPES = [
        ('texte', 'Texte'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
    ]

    # Auteure
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    prenom      = models.CharField(max_length=60)
    pays        = models.CharField(max_length=60, blank=True)
    formule     = models.CharField(max_length=4, blank=True)

    # Type de témoignage
    type_temo   = models.CharField(max_length=10, choices=TYPES, default='texte')

    # Contenu
    texte       = models.TextField(blank=True)
    note        = models.IntegerField(choices=NOTES, default=5)

    # Vidéo
    video_url   = models.URLField(blank=True)
    video_fichier = models.FileField(upload_to='temoignages/videos/', blank=True, null=True)

    # Audio
    audio_fichier = models.FileField(upload_to='temoignages/audios/', blank=True, null=True)

    # Photos
    photo_avant = models.ImageField(upload_to='temoignages/avant/', blank=True, null=True)
    photo_apres = models.ImageField(upload_to='temoignages/apres/', blank=True, null=True)

    # Gestion
    statut      = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    en_vedette  = models.BooleanField(default=False)
    date        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.prenom} — {self.type_temo} — {self.note}★ ({self.statut})"
