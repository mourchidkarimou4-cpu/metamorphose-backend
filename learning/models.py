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
