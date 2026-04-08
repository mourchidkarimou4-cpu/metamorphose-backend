from django.db import models
from django.conf import settings


class Transaction(models.Model):
    STATUTS = [
        ("pending", "En attente"),
        ("success", "Succès"),
        ("failed",  "Échec"),
    ]
    SOURCES = [
        ("checkout", "Initié par le membre"),
        ("webhook",  "Confirmé par webhook"),
        ("manual",   "Activation manuelle admin"),
    ]
    user           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="transactions",
    )
    transaction_id = models.CharField(max_length=200, unique=True, db_index=True)
    formule        = models.CharField(max_length=4, blank=True)
    montant        = models.PositiveIntegerField(default=0)
    statut         = models.CharField(max_length=20, choices=STATUTS, default="pending")
    source         = models.CharField(max_length=20, choices=SOURCES, default="checkout")
    email_client   = models.EmailField(blank=True)
    details        = models.JSONField(default=dict, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ["-created_at"]
        verbose_name        = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.transaction_id} — {self.get_statut_display()} — {self.montant} FCFA"
