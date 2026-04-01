from django.db import models

class SiteConfig(models.Model):
    """Contenu éditable du site en temps réel"""
    cle     = models.CharField(max_length=100, unique=True)
    valeur  = models.TextField()
    section = models.CharField(max_length=60, default='general')

    def __str__(self):
        return f"{self.section} · {self.cle}"

    @classmethod
    def get(cls, cle, defaut=''):
        try:
            return cls.objects.get(cle=cle).valeur
        except cls.DoesNotExist:
            return defaut

class ListeAttente(models.Model):
    email   = models.EmailField(unique=True)
    prenom  = models.CharField(max_length=60, blank=True)
    date    = models.DateTimeField(auto_now_add=True)
    notifie = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.prenom} — {self.email}"