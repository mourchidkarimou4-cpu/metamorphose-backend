from django.conf import settings
from django.db import models


class Categorie(models.Model):
    nom     = models.CharField(max_length=100)
    slug    = models.SlugField(unique=True)
    icone   = models.CharField(max_length=10, default='✦')
    couleur = models.CharField(max_length=20, default='#C9A96A')
    ordre   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom


class Cours(models.Model):
    FORMATS = [
        ('texte', 'Article'),
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('pdf',   'PDF'),
    ]
    NIVEAUX = [
        ('debutant',      'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance',        'Avancé'),
    ]

    titre       = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    description = models.TextField()
    categorie   = models.ForeignKey(Categorie, on_delete=models.SET_NULL,
                                    null=True, related_name='cours')
    semaine     = models.PositiveIntegerField(null=True, blank=True)
    format      = models.CharField(max_length=10, choices=FORMATS, default='texte')
    contenu     = models.TextField(blank=True)
    video_url   = models.URLField(blank=True)
    audio_url   = models.URLField(blank=True)
    pdf_url     = models.URLField(blank=True)
    duree       = models.CharField(max_length=20, blank=True)
    niveau      = models.CharField(max_length=20, choices=NIVEAUX, default='debutant')
    image       = models.CharField(max_length=500, blank=True)
    actif       = models.BooleanField(default=True)
    en_vedette  = models.BooleanField(default=False)
    ordre       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre', '-created_at']

    def __str__(self):
        return self.titre

class AccesCours(models.Model):
    """
    Accès d'une utilisatrice à un cours spécifique du Store.
    Activé manuellement par Coach Prélia APEDO AHONON ou automatiquement via webhook.
    """
    SOURCES = [
        ('manuel',   'Activation manuelle — Coach Prélia APEDO AHONON'),
        ('webhook',  'Confirmation automatique — Webhook'),
        ('offert',   'Offert par Coach Prélia APEDO  AHONON'),
    ]
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='acces_cours'
    )
    cours      = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name='acces'
    )
    source     = models.CharField(max_length=20, choices=SOURCES, default='manuel')
    actif      = models.BooleanField(default=True)
    transaction= models.ForeignKey(
        'paiement.Transaction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='acces_cours'
    )
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'cours']
        verbose_name = "Acces Cours"
        verbose_name_plural = "Acces Cours"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} → {self.cours.titre} ({self.get_source_display()})"
