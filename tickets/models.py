import uuid
from django.db import models
from django.conf import settings


class Evenement(models.Model):
    nom         = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    date        = models.DateTimeField()
    lieu        = models.CharField(max_length=200, blank=True)
    places_total= models.PositiveIntegerField(default=50)
    prix        = models.PositiveIntegerField(default=0, help_text="En FCFA, 0 = gratuit")
    image       = models.CharField(max_length=500, blank=True)
    actif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.nom

    @property
    def places_restantes(self):
        return max(0, self.places_total - self.tickets.filter(
            statut__in=['valide', 'scanne']
        ).count())

    @property
    def complet(self):
        return self.places_restantes == 0


class Ticket(models.Model):
    STATUTS = [
        ('valide',   'Valide'),
        ('scanne',   'Scanné'),
        ('annule',   'Annulé'),
    ]

    evenement   = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='tickets')
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tickets'
    )
    # Pour les non-membres
    nom         = models.CharField(max_length=100, blank=True)
    email       = models.EmailField()
    telephone   = models.CharField(max_length=20, blank=True)

    code        = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    statut      = models.CharField(max_length=10, choices=STATUTS, default='valide')
    scanne_le   = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom_complet} — {self.evenement.nom} — {self.get_statut_display()}"

    @property
    def nom_complet(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email
        return self.nom or self.email
