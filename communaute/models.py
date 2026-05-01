from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
import cloudinary.models
import uuid

class CleAcces(models.Model):
    utilisatrice       = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cle_communaute')
    cle                = models.CharField(max_length=32, unique=True, db_index=True)
    active             = models.BooleanField(default=True)
    premiere_connexion = models.BooleanField(default=True)
    creee_le           = models.DateTimeField(auto_now_add=True)
    utilisee_le        = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Clé d'accès communauté"

    def __str__(self):
        return f"{self.utilisatrice.email} — {self.cle}"

    @classmethod
    def generer(cls, utilisatrice):
        cle = get_random_string(32)
        obj, _ = cls.objects.update_or_create(
            utilisatrice=utilisatrice,
            defaults={'cle': cle, 'active': True, 'premiere_connexion': True}
        )
        return obj

class Publication(models.Model):
    TYPES = [('texte','Texte'),('photo','Photo'),('video','Vidéo')]
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auteure    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publications')
    contenu    = models.TextField()
    type_media = models.CharField(max_length=10, choices=TYPES, default='texte')
    media      = cloudinary.models.CloudinaryField('media', resource_type='auto', folder='metamorphose/communaute', blank=True, null=True)
    pour_coach = models.BooleanField(default=False)
    epingle    = models.BooleanField(default=False)
    visible    = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-epingle', '-created_at']

    def __str__(self):
        return f"{self.auteure.email} — {self.contenu[:50]}"

class Commentaire(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='commentaires')
    auteure     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commentaires')
    contenu     = models.TextField()
    est_coach   = models.BooleanField(default=False)
    visible     = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.auteure.email} → {str(self.publication.id)[:8]}"

class ProfilCommunaute(models.Model):
    utilisatrice        = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_communaute')
    presentation        = models.TextField(blank=True)
    secteur             = models.CharField(max_length=100, blank=True)
    pays                = models.CharField(max_length=100, blank=True)
    situation_mat       = models.CharField(max_length=100, blank=True)
    passion             = models.TextField(blank=True)
    apport_metamorphose = models.TextField(blank=True)
    attentes            = models.TextField(blank=True)
    onboarding_fait     = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profil — {self.utilisatrice.email}"

class CleAccesEmail(models.Model):
    """Clé d'accès pour un email sans compte membre."""
    email    = models.EmailField(unique=True, db_index=True)
    cle      = models.CharField(max_length=32, unique=True)
    active   = models.BooleanField(default=True)
    creee_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Clé accès email externe"

    def __str__(self):
        return f"{self.email} — {self.cle}"

    @classmethod
    def generer(cls, email):
        from django.utils.crypto import get_random_string
        cle = get_random_string(32)
        obj, _ = cls.objects.update_or_create(
            email=email,
            defaults={'cle': cle, 'active': True}
        )
        return obj
