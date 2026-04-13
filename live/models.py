from django.db import models
from django.conf import settings
import uuid

class Salle(models.Model):
    STATUT = [('attente','En attente'),('active','Active'),('terminee','Terminée')]
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    hote        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='salles_hote')
    mot_de_passe= models.CharField(max_length=50, blank=True)
    statut      = models.CharField(max_length=20, choices=STATUT, default='attente')
    max_participants = models.IntegerField(default=1000)
    mode        = models.CharField(max_length=20, default='reunion', choices=[
        ('reunion','Réunion'),('webinaire','Webinaire'),('live','Live')
    ])
    enregistrement_actif = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    started_at  = models.DateTimeField(null=True, blank=True)
    ended_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} ({self.statut})"

class Participant(models.Model):
    salle       = models.ForeignKey(Salle, on_delete=models.CASCADE, related_name='participants')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    nom         = models.CharField(max_length=100)
    role        = models.CharField(max_length=20, default='participant', choices=[
        ('hote','Hôte'),('coanimateur','Co-animateur'),('participant','Participant'),('spectateur','Spectateur')
    ])
    rejoint_at  = models.DateTimeField(auto_now_add=True)
    quitte_at   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} — {self.salle.titre}"

class Message(models.Model):
    salle       = models.ForeignKey(Salle, on_delete=models.CASCADE, related_name='messages')
    auteur      = models.CharField(max_length=100)
    contenu     = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
