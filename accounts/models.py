from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    pays = models.CharField(max_length=60, blank=True)
    formule = models.CharField(max_length=10, blank=True,
        choices=[('F1','Live Groupe'),('F2','Live Privé'),
                 ('F3','Présentiel Groupe'),('F4','Présentiel Privé')])
    actif = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
