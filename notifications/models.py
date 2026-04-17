from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# ══════════════════════════════════════════════════════════════════
# 1. NOTIFICATIONS ADMIN
# ══════════════════════════════════════════════════════════════════
class Notification(models.Model):
    """Notification visible dans le dashboard admin de Prélia."""
    TYPES = [
        ('inscription',   'Nouvelle inscription'),
        ('temoignage',    'Nouveau témoignage'),
        ('contact',       'Nouveau message'),
        ('paiement',      'Paiement reçu'),
        ('ticket',        'Nouveau ticket'),
        ('satisfaction',  'Formulaire satisfaction'),
        ('message',       'Message membre'),
        ('system',        'Système'),
    ]
    type        = models.CharField(max_length=20, choices=TYPES)
    titre       = models.CharField(max_length=200)
    message     = models.TextField()
    lien        = models.CharField(max_length=200, blank=True)
    lu          = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications_generees')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'

    def __str__(self):
        return f"[{self.type}] {self.titre}"


# ══════════════════════════════════════════════════════════════════
# 2. MESSAGERIE INTERNE Prélia ↔ Membres
# ══════════════════════════════════════════════════════════════════
class Conversation(models.Model):
    """Thread de conversation entre Prélia et un membre."""
    membre      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='conversation')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    non_lu_admin   = models.IntegerField(default=0)  # msgs non lus par Prélia
    non_lu_membre  = models.IntegerField(default=0)  # msgs non lus par le membre

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conv — {self.membre.email}"


class Message(models.Model):
    """Message dans une conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    contenu      = models.TextField()
    est_admin    = models.BooleanField(default=False)  # True = envoyé par Prélia
    lu           = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.expediteur.email} → {self.created_at:%d/%m %H:%M}"


# ══════════════════════════════════════════════════════════════════
# 3. PLANIFICATEUR DE VAGUES
# ══════════════════════════════════════════════════════════════════
class Vague(models.Model):
    """Une vague du programme Méta'Morph'Ose."""
    STATUTS = [
        ('planifiee',  'Planifiée'),
        ('active',     'En cours'),
        ('terminee',   'Terminée'),
    ]
    nom          = models.CharField(max_length=100)
    numero       = models.PositiveIntegerField(unique=True)
    date_debut   = models.DateField()
    date_fin     = models.DateField()
    statut       = models.CharField(max_length=20, choices=STATUTS, default='planifiee')
    places_max   = models.PositiveIntegerField(default=30)
    description  = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-numero']
        verbose_name = 'Vague'

    def __str__(self):
        return f"Vague {self.numero} — {self.nom}"

    @property
    def places_prises(self):
        return self.membres.count()

    @property
    def places_restantes(self):
        return max(0, self.places_max - self.places_prises)


class MembreVague(models.Model):
    """Affectation d'un membre à une vague."""
    vague      = models.ForeignKey(Vague, on_delete=models.CASCADE, related_name='membres')
    membre     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vagues')
    date_ajout = models.DateTimeField(auto_now_add=True)
    notes      = models.TextField(blank=True)

    class Meta:
        unique_together = ['vague', 'membre']

    def __str__(self):
        return f"{self.membre.email} → Vague {self.vague.numero}"


# ══════════════════════════════════════════════════════════════════
# 4. PROGRESSION MEMBRE
# ══════════════════════════════════════════════════════════════════
class Progression(models.Model):
    """Suivi de la progression d'un membre dans le programme."""
    membre        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progression')
    semaine_actuelle = models.PositiveIntegerField(default=1)
    sessions_completees = models.PositiveIntegerField(default=0)
    sessions_total = models.PositiveIntegerField(default=16)  # 2/semaine × 8 semaines
    notes_coach    = models.TextField(blank=True)
    objectifs      = models.TextField(blank=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Progression'

    def __str__(self):
        return f"Progression — {self.membre.email}"

    @property
    def pourcentage(self):
        if self.sessions_total == 0:
            return 0
        return round((self.sessions_completees / self.sessions_total) * 100)

    @property
    def badges(self):
        b = []
        if self.sessions_completees >= 1:  b.append('premiere_session')
        if self.semaine_actuelle >= 4:     b.append('mi_parcours')
        if self.sessions_completees >= self.sessions_total: b.append('programme_complete')
        return b


# ══════════════════════════════════════════════════════════════════
# 5. FORMULAIRE SATISFACTION J+30
# ══════════════════════════════════════════════════════════════════
class FormulaireSatisfaction(models.Model):
    """Formulaire de satisfaction envoyé automatiquement à J+30."""
    membre        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='satisfaction')
    envoye_le     = models.DateTimeField(null=True, blank=True)
    complete_le   = models.DateTimeField(null=True, blank=True)
    # Réponses
    note_globale       = models.IntegerField(null=True, blank=True)  # 1-10
    note_coach         = models.IntegerField(null=True, blank=True)
    note_contenu       = models.IntegerField(null=True, blank=True)
    note_transformation= models.IntegerField(null=True, blank=True)
    point_fort         = models.TextField(blank=True)
    point_ameliorer    = models.TextField(blank=True)
    recommanderait     = models.BooleanField(null=True, blank=True)
    commentaire_libre  = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Formulaire satisfaction'

    def __str__(self):
        return f"Satisfaction — {self.membre.email} — {'Complété' if self.complete_le else 'En attente'}"


# ══════════════════════════════════════════════════════════════════
# 6. AGENDA COACH
# ══════════════════════════════════════════════════════════════════
class SessionAgenda(models.Model):
    """Session planifiée dans l'agenda de Prélia."""
    TYPES = [
        ('live_groupe',    'Live Groupe'),
        ('live_prive',     'Live Privé'),
        ('masterclass',    'Masterclass'),
        ('reunion',        'Réunion interne'),
        ('autre',          'Autre'),
    ]
    titre           = models.CharField(max_length=200)
    type_session    = models.CharField(max_length=20, choices=TYPES)
    date_debut      = models.DateTimeField()
    date_fin        = models.DateTimeField()
    description     = models.TextField(blank=True)
    lien_live       = models.URLField(blank=True)
    rappel_envoye   = models.BooleanField(default=False)
    membres_invites = models.ManyToManyField(User, blank=True, related_name='sessions_invitees')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_debut']
        verbose_name = 'Session agenda'

    def __str__(self):
        return f"{self.titre} — {self.date_debut:%d/%m/%Y %H:%M}"
