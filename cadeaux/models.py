from django.db import models
import uuid
import string, random

def gen_code():
    chars = string.ascii_uppercase + string.digits
    return "MMO-" + "".join(random.choices(chars, k=8))

class CartesCadeaux(models.Model):
    FORMULES = [
        ('F1','Live · Groupe'),
        ('F2','Live · Privé'),
        ('F3','Présentiel · Groupe'),
        ('F4','Présentiel · Privé'),
    ]
    STATUTS = [
        ('en_attente','En attente'),
        ('payee','Payée'),
        ('utilisee','Utilisée'),
        ('expiree','Expirée'),
    ]

    code            = models.CharField(max_length=20, unique=True, default=gen_code)
    formule         = models.CharField(max_length=4, choices=FORMULES)

    # Acheteur
    acheteur_nom    = models.CharField(max_length=100)
    acheteur_email  = models.EmailField()
    acheteur_tel    = models.CharField(max_length=20, blank=True)

    # Destinataire
    destinataire_nom   = models.CharField(max_length=100)
    destinataire_email = models.EmailField(blank=True)
    occasion           = models.CharField(max_length=100, blank=True)
    message_perso      = models.TextField(blank=True)

    # Gestion
    statut          = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateField(null=True, blank=True)
    date_utilisation= models.DateTimeField(null=True, blank=True)
    utilisee_par    = models.EmailField(blank=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.code} — {self.destinataire_nom} ({self.get_formule_display()})"
