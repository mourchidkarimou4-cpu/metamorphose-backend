from django.db import models
from django.conf import settings

class ReunionZoom(models.Model):
    STATUT = [('attente','En attente'),('active','Active'),('terminee','Terminée')]
    
    titre        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    meeting_id   = models.CharField(max_length=100, unique=True)
    password     = models.CharField(max_length=50, blank=True)
    join_url     = models.URLField(blank=True)
    start_url    = models.URLField(max_length=1000, blank=True)
    hote         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reunions_zoom')
    statut       = models.CharField(max_length=20, choices=STATUT, default='attente')
    date_debut   = models.DateTimeField(null=True, blank=True)
    duree        = models.IntegerField(default=60, help_text='Durée en minutes')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} ({self.meeting_id})"
