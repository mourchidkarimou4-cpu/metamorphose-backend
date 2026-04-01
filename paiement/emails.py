# Ajouter dans accounts/views.py ou nouveau fichier emails.py
# Emails automatiques via Django

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def envoyer_email_confirmation_inscription(user, formule_label):
    """Email envoyé après soumission du formulaire d'inscription"""
    sujet = "Votre demande d'inscription — Méta'Morph'Ose"
    message = f"""
Bonjour {user.first_name or user.email},

Votre demande d'inscription au programme Méta'Morph'Ose — formule {formule_label} a bien été reçue.

Prélia vous contactera sous 24 à 48h pour confirmer votre place et vous communiquer les détails de démarrage.

En attendant, n'hésitez pas à consulter le programme :
https://metamorphose.com/programme

À très bientôt,
Prélia Apedo — Méta'Morph'Ose
    """
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass

def envoyer_email_confirmation_paiement(user, formule_label, montant):
    """Email envoyé après paiement confirmé"""
    sujet = "Paiement confirmé — Bienvenue dans Méta'Morph'Ose !"
    message = f"""
Bonjour {user.first_name or user.email},

Votre paiement de {montant:,} FCFA pour la formule {formule_label} a été confirmé.

Votre accès à l'espace membre est maintenant actif.

Connectez-vous ici : https://metamorphose.com/espace-membre

Vous y trouverez :
- Vos replays de sessions
- Vos 7 guides PDF bonus
- L'accès au Club des Métamorphosées

Bienvenue dans l'aventure,
Prélia Apedo — Méta'Morph'Ose
    """
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass

def envoyer_email_admin_nouvelle_inscription(admin_email, user, formule_label):
    """Notifie Prélia d'une nouvelle inscription"""
    sujet = f"Nouvelle inscription — {user.first_name or user.email} ({formule_label})"
    message = f"""
Nouvelle demande d'inscription sur Méta'Morph'Ose.

Nom     : {user.first_name} {user.last_name}
Email   : {user.email}
WhatsApp: {user.whatsapp or 'Non renseigné'}
Pays    : {user.pays or 'Non renseigné'}
Formule : {formule_label}

Gérer depuis le dashboard : https://metamorphose.com/admin
    """
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception:
        pass
