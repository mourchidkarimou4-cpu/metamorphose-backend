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
        ('appel_decouverte', 'Appel Découverte'),
        ('bilan_image',      'Bilan Image'),
        ('seance_coaching',  'Séance de Coaching'),
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
    NB_SEANCES = [
        ('1', '1 séance'),
        ('2', '2 séances'),
        ('3+', '3 séances ou plus'),
    ]
    # Durées en minutes (incluant pause 30min)
    DUREES_BLOQUEES = {
        'appel_decouverte': 60,   # 30min + 30min pause
        'bilan_image':      90,   # 60min + 30min pause
        'seance_coaching':  150,  # 120min + 30min pause
    }
    # Prix selon type et mode
    PRIX = {
        'appel_decouverte': {'en_ligne': 0,     'presentiel': None},
        'bilan_image':      {'en_ligne': 32500,  'presentiel': 60000},
        'seance_coaching':  {'en_ligne': 40000,  'presentiel': 70000},
    }

    prenom      = models.CharField(max_length=100)
    nom         = models.CharField(max_length=100)
    email       = models.EmailField()
    whatsapp    = models.CharField(max_length=30)
    pays        = models.CharField(max_length=100, blank=True)

    type_rdv    = models.CharField(max_length=30, choices=TYPES)
    mode        = models.CharField(max_length=20, choices=MODES)
    nb_seances  = models.CharField(max_length=5, choices=NB_SEANCES, default='1', blank=True)
    prix        = models.PositiveIntegerField(default=0)
    date        = models.DateField()
    heure       = models.TimeField()
    message     = models.TextField(blank=True)

    statut        = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    paiement_recu = models.BooleanField(default=False)
    note_admin    = models.TextField(blank=True)
    lien_reunion  = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-heure']
        verbose_name = 'Rendez-vous'

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.date} {self.heure}"

    @property
    def est_gratuit(self):
        return self.type_rdv == 'appel_decouverte'

    @property
    def duree_bloquee(self):
        return self.DUREES_BLOQUEES.get(self.type_rdv, 60)

    @property
    def duree_rdv(self):
        durees = {
            'appel_decouverte': 30,
            'bilan_image':      60,
            'seance_coaching':  120,
        }
        return durees.get(self.type_rdv, 30)
