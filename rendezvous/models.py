from django.db import models

class Disponibilite(models.Model):
    JOURS = [
        ('lundi','Lundi'),('mardi','Mardi'),('mercredi','Mercredi'),
        ('jeudi','Jeudi'),('vendredi','Vendredi'),('samedi','Samedi'),('dimanche','Dimanche'),
    ]
    jour        = models.CharField(max_length=20, choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin   = models.TimeField()
    actif       = models.BooleanField(default=True)

    class Meta:
        ordering = ['jour','heure_debut']
        verbose_name = 'Disponibilité'

    def __str__(self):
        return f"{self.jour} {self.heure_debut}–{self.heure_fin}"


class RendezVous(models.Model):
    TYPES = [
        ('decouverte',   'Appel Découverte'),
        ('coaching',     'Séance de Coaching'),
        ('consultation', 'Consultation Image & Style'),
    ]
    MODES = [
        ('en_ligne',   'En ligne'),
        ('presentiel', 'En présentiel'),
    ]
    STATUTS = [
        ('en_attente', 'En attente'),
        ('confirme',   'Confirmé'),
        ('refuse',     'Refusé'),
        ('annule',     'Annulé'),
    ]
    DUREES = {
        'decouverte':   20,
        'coaching':     60,
        'consultation': 45,
    }

    prenom   = models.CharField(max_length=100)
    nom      = models.CharField(max_length=100)
    email    = models.EmailField()
    whatsapp = models.CharField(max_length=30)
    pays     = models.CharField(max_length=100, blank=True)

    type_rdv = models.CharField(max_length=20, choices=TYPES)
    mode     = models.CharField(max_length=20, choices=MODES)
    date     = models.DateField()
    heure    = models.TimeField()
    message  = models.TextField(blank=True)

    statut        = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    paiement_recu = models.BooleanField(default=False)
    note_admin    = models.TextField(blank=True)
    lien_reunion  = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-heure']
        verbose_name = 'Rendez-vous'
        unique_together = [['date', 'heure']]

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.date} {self.heure}"

    @property
    def est_gratuit(self):
        return self.type_rdv == 'decouverte'

    @property
    def duree(self):
        return self.DUREES.get(self.type_rdv, 30)
