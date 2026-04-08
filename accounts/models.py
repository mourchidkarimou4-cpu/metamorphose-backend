from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    email    = models.EmailField(unique=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    pays     = models.CharField(max_length=60, blank=True)
    formule  = models.CharField(
        max_length=10, blank=True,
        choices=[
            ('F1', 'Live Groupe'),
            ('F2', 'Live Privé'),
            ('F3', 'Présentiel Groupe'),
            ('F4', 'Présentiel Privé'),
        ]
    )
    actif = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    user       = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token      = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used       = models.BooleanField(default=False)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Token de réinitialisation'
        verbose_name_plural = 'Tokens de réinitialisation'

    def __str__(self):
        return f"Reset token — {self.user.email} — {'utilisé' if self.used else 'valide'}"

    def is_valid(self):
        if self.used:
            return False
        return (timezone.now() - self.created_at) < timedelta(hours=1)

    @classmethod
    def purge_expired(cls):
        cutoff = timezone.now() - timedelta(hours=2)
        cls.objects.filter(
            models.Q(used=True) | models.Q(created_at__lt=cutoff)
        ).delete()
