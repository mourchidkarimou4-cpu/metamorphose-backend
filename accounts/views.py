import secrets
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from .models import PasswordResetToken
from .serializers import RegisterSerializer, UserSerializer, ContactSerializer

User   = get_user_model()
logger = logging.getLogger(__name__)


class LoginThrottle(AnonRateThrottle):
    scope = 'login'
    rate  = '10/hour'

class RegisterThrottle(AnonRateThrottle):
    scope = 'register'
    rate  = '5/hour'

class ContactThrottle(AnonRateThrottle):
    scope = 'contact'
    rate  = '3/hour'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register(request):
    s = RegisterSerializer(data=request.data)
    if s.is_valid():
        user    = s.save()
        refresh = RefreshToken.for_user(user)
        try:
            _email_bienvenue(user)
        except Exception as e:
            logger.warning(f"Email bienvenue non envoyé à {user.email} : {e}")
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
# TODO(sécurité) : les tokens JWT sont stockés en localStorage côté React.
# Pour V2, migrer vers httpOnly cookies (SameSite=Strict) pour éliminer le risque XSS.
def login(request):
    email    = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    if not email or not password:
        return Response({'detail': 'Email et mot de passe requis.'}, status=400)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Aucun compte avec cet email.'}, status=404)
    if not user.check_password(password):
        return Response({'detail': 'Mot de passe incorrect.'}, status=400)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access':  str(refresh.access_token),
        'refresh': str(refresh),
        'user':    UserSerializer(user).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ContactThrottle])
def contact(request):
    from contenu.models import DemandeContact
    s = ContactSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=400)
    d = s.validated_data
    DemandeContact.objects.create(**d)
    try:
        send_mail(
            subject=f"Nouvelle demande — {d['prenom']} {d['nom']} ({d.get('formule','?')})",
            message=(
                f"Prénom : {d['prenom']}\nNom : {d['nom']}\n"
                f"Email : {d['email']}\nWhatsApp : {d.get('whatsapp','')}\n"
                f"Pays : {d.get('pays','')}\nFormule : {d.get('formule','')}\n\n"
                f"Message :\n{d.get('message','')}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        logger.warning(f"Email contact admin non envoyé : {e}")
    return Response({'detail': 'Demande reçue.'}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def confirmer_paiement(request):
    """
    Appelée quand la cliente déclare avoir effectué son paiement.
    Envoie un email de reçu à la cliente + notification à Prélia.
    """
    from contenu.models import DemandeContact
    from django.utils import timezone

    data = request.data
    prenom   = data.get("prenom", "")
    nom      = data.get("nom", "")
    email    = data.get("email", "")
    whatsapp = data.get("whatsapp", "")
    pays     = data.get("pays", "")
    formule  = data.get("formule", "")
    message  = data.get("message", "")

    FORMULES = {
        "F1": {"label": "ESSENTIELLE",   "prix": "70 000 FCFA",  "desc": "Accompagnement de groupe en ligne"},
        "F2": {"label": "PERSONNALISÉE", "prix": "160 000 FCFA", "desc": "Accompagnement individuel en ligne"},
        "F3": {"label": "IMMERSION",     "prix": "267 000 FCFA", "desc": "Accompagnement de groupe en présentiel"},
        "F4": {"label": "VIP",           "prix": "370 000 FCFA", "desc": "Accompagnement individuel en présentiel"},
    }

    f = FORMULES.get(formule, {"label": formule, "prix": "—", "desc": ""})
    date_str = timezone.now().strftime("%d/%m/%Y à %Hh%M")

    # ── Sauvegarder la demande avec statut paiement déclaré ──
    try:
        DemandeContact.objects.create(
            prenom=prenom, nom=nom, email=email,
            whatsapp=whatsapp, pays=pays, formule=formule,
            message=f"[PAIEMENT DÉCLARÉ le {date_str}] {message}"
        )
    except Exception as e:
        logger.warning(f"Erreur sauvegarde demande paiement : {e}")

    # ── Email HTML reçu cliente ──────────────────────────────
    email_cliente_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Confirmation de paiement — Méta'Morph'Ose</title>
</head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:40px 20px;">

    <!-- En-tête -->
    <div style="text-align:center;margin-bottom:40px;">
      <h1 style="font-family:Georgia,serif;font-size:28px;color:#F8F5F2;margin:0;font-weight:400;">
        Méta'<span style="color:#C9A96A;">Morph'</span><span style="color:#C2185B;">Ose</span>
      </h1>
      <p style="color:rgba(248,245,242,.4);font-size:11px;letter-spacing:3px;text-transform:uppercase;margin:8px 0 0;">
        Programme de transformation féminine
      </p>
    </div>

    <!-- Carte principale -->
    <div style="background:#111111;border:1px solid rgba(201,169,106,.2);border-radius:8px;padding:40px;margin-bottom:24px;">

      <!-- Icône succès -->
      <div style="text-align:center;margin-bottom:32px;">
        <div style="width:64px;height:64px;border-radius:50%;background:rgba(76,175,80,.1);border:2px solid #4CAF50;display:inline-flex;align-items:center;justify-content:center;">
          <span style="color:#4CAF50;font-size:28px;">✓</span>
        </div>
      </div>

      <h2 style="font-family:Georgia,serif;font-size:24px;color:#F8F5F2;text-align:center;margin:0 0 8px;font-weight:600;">
        Paiement déclaré avec succès
      </h2>
      <p style="color:rgba(248,245,242,.5);text-align:center;font-size:14px;margin:0 0 32px;">
        Bonjour {prenom}, merci pour votre confiance.
      </p>

      <!-- Séparateur or -->
      <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(201,169,106,.4),transparent);margin-bottom:32px;"></div>

      <!-- Détails du reçu -->
      <h3 style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:rgba(201,169,106,.6);margin:0 0 20px;">
        Récapitulatif
      </h3>

      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">Nom complet</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:13px;text-align:right;font-weight:500;">{prenom} {nom}</td>
        </tr>
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">Email</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:13px;text-align:right;">{email}</td>
        </tr>
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">WhatsApp</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:13px;text-align:right;">{whatsapp}</td>
        </tr>
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">Pays</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:13px;text-align:right;">{pays}</td>
        </tr>
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">Formule</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#C2185B;font-size:13px;text-align:right;font-weight:600;">{f["label"]}</td>
        </tr>
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:13px;">Description</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:13px;text-align:right;">{f["desc"]}</td>
        </tr>
        <tr>
          <td style="padding:16px 0 0;color:rgba(248,245,242,.4);font-size:13px;">Montant déclaré</td>
          <td style="padding:16px 0 0;color:#C9A96A;font-size:20px;text-align:right;font-weight:700;">{f["prix"]}</td>
        </tr>
        <tr>
          <td style="padding:8px 0 0;color:rgba(248,245,242,.4);font-size:12px;">Date de déclaration</td>
          <td style="padding:8px 0 0;color:rgba(248,245,242,.5);font-size:12px;text-align:right;">{date_str}</td>
        </tr>
      </table>

      <!-- Séparateur -->
      <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(201,169,106,.4),transparent);margin:32px 0;"></div>

      <!-- Message important -->
      <div style="background:rgba(201,169,106,.06);border:1px solid rgba(201,169,106,.15);border-radius:4px;padding:20px;">
        <p style="color:#C9A96A;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:0 0 8px;">Prochaine étape</p>
        <p style="color:rgba(248,245,242,.7);font-size:14px;line-height:1.8;margin:0;">
          Prélia APEDO AHONON va vérifier votre paiement et vous contacter sous <strong style="color:#F8F5F2;">24 à 48 heures</strong> 
          sur WhatsApp pour confirmer votre place et vous donner accès au programme.
        </p>
      </div>
    </div>

    <!-- Contact -->
    <div style="background:#111111;border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:24px;margin-bottom:24px;text-align:center;">
      <p style="color:rgba(248,245,242,.4);font-size:12px;margin:0 0 12px;">Pour toute question urgente</p>
      <a href="https://wa.me/22901961140" style="color:#C9A96A;font-size:13px;text-decoration:none;display:block;margin-bottom:6px;">
        WhatsApp : +229 01 96 11 40 93
      </a>
      <a href="mailto:whiteblackdress22@gmail.com" style="color:#C9A96A;font-size:13px;text-decoration:none;">
        whiteblackdress22@gmail.com
      </a>
    </div>

    <!-- Footer -->
    <div style="text-align:center;">
      <p style="font-family:Georgia,serif;font-style:italic;color:rgba(201,169,106,.4);font-size:14px;margin:0;">
        Votre renaissance commence ici.
      </p>
      <p style="color:rgba(248,245,242,.2);font-size:11px;margin:12px 0 0;">
        © 2026 Méta'Morph'Ose · White & Black · Prélia APEDO AHONON
      </p>
    </div>

  </div>
</body>
</html>
"""

    # ── Email notification Prélia ────────────────────────────
    email_prelia_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Nouveau paiement déclaré</title></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:32px 16px;">
    <div style="background:#fff;border-radius:8px;padding:32px;border:1px solid #e0e0e0;">
      <h2 style="color:#C2185B;margin:0 0 8px;font-size:20px;">Nouveau paiement déclaré</h2>
      <p style="color:#666;font-size:13px;margin:0 0 24px;">{date_str}</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr style="background:#f9f9f9;">
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Nom</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;font-weight:600;">{prenom} {nom}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Email</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;">{email}</td>
        </tr>
        <tr style="background:#f9f9f9;">
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">WhatsApp</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;">{whatsapp}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Pays</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;">{pays}</td>
        </tr>
        <tr style="background:#f9f9f9;">
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Formule</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#C2185B;font-weight:700;">{f["label"]}</td>
        </tr>
        <tr>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Montant</td>
          <td style="padding:10px 14px;border:1px solid #eee;font-size:16px;color:#C9A96A;font-weight:700;">{f["prix"]}</td>
        </tr>
        {'<tr style="background:#f9f9f9;"><td style="padding:10px 14px;border:1px solid #eee;font-size:13px;color:#666;">Message</td><td style="padding:10px 14px;border:1px solid #eee;font-size:13px;">' + message + '</td></tr>' if message else ''}
      </table>
      <div style="margin-top:24px;padding:16px;background:#fff3e0;border-radius:4px;border-left:4px solid #C9A96A;">
        <p style="margin:0;font-size:13px;color:#666;">
          <strong>Action requise :</strong> Vérifiez le paiement de {prenom} dans votre application de paiement, 
          puis confirmez son accès au programme dans le dashboard admin.
        </p>
      </div>
    </div>
  </div>
</body>
</html>
"""

    # ── Envoi des emails ─────────────────────────────────────
    from django.core.mail import EmailMultiAlternatives

    # Email à la cliente
    if email:
        try:
            msg_cliente = EmailMultiAlternatives(
                subject=f"Méta'Morph'Ose · Confirmation de paiement — Formule {f['label']}",
                body=f"Bonjour {prenom},\n\nVotre paiement de {f['prix']} pour la formule {f['label']} a bien été déclaré.\nPrélia vous contactera sous 24-48h.\n\nMéta'Morph'Ose",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg_cliente.attach_alternative(email_cliente_html, "text/html")
            msg_cliente.send(fail_silently=True)
        except Exception as e:
            logger.warning(f"Email reçu cliente non envoyé : {e}")

    # Email à Prélia
    try:
        admin_email = settings.ADMIN_EMAIL or settings.EMAIL_HOST_USER
        if admin_email:
            msg_admin = EmailMultiAlternatives(
                subject=f"[MMO] Paiement déclaré — {prenom} {nom} · {f['label']} · {f['prix']}",
                body=f"Nouveau paiement déclaré par {prenom} {nom} ({email}) pour la formule {f['label']} à {f['prix']}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_email],
            )
            msg_admin.attach_alternative(email_prelia_html, "text/html")
            msg_admin.send(fail_silently=True)
    except Exception as e:
        logger.warning(f"Email notification Prélia non envoyé : {e}")

    return Response({
        "detail": "Paiement déclaré. Email de confirmation envoyé.",
        "prenom": prenom,
        "formule": f["label"],
        "montant": f["prix"],
    }, status=201)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    import re
    user      = request.user
    email     = request.data.get("email", user.email).strip().lower()
    firstName = request.data.get("first_name", user.first_name)
    lastName  = request.data.get("last_name", user.last_name)
    whatsapp  = request.data.get("whatsapp", user.whatsapp)
    pays      = request.data.get("pays", user.pays)

    # Validation format email
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return Response({"detail": "Format d'email invalide."}, status=400)

    from accounts.models import CustomUser
    if CustomUser.objects.exclude(pk=user.pk).filter(email__iexact=email).exists():
        return Response({"detail": "Cet email est déjà utilisé."}, status=400)

    user.email      = email
    user.first_name = firstName
    user.last_name  = lastName
    user.whatsapp   = whatsapp or user.whatsapp
    user.pays       = pays or user.pays
    user.save()
    return Response({
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "whatsapp":   user.whatsapp,
        "pays":       user.pays,
        "is_staff":   user.is_staff,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user         = request.user
    old_password = request.data.get("old_password", "")
    new_password = request.data.get("new_password", "")
    if not user.check_password(old_password):
        return Response({"detail": "Ancien mot de passe incorrect."}, status=400)
    if len(new_password) < 8:
        return Response({"detail": "Le mot de passe doit contenir au moins 8 caractères."}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({"detail": "Mot de passe modifié avec succès."})


@api_view(["POST"])
@permission_classes([AllowAny])
def demander_reset(request):
    email = request.data.get("email", "").strip().lower()
    try:
        user  = User.objects.get(email=email)
        token = secrets.token_urlsafe(48)
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
        PasswordResetToken.objects.create(user=user, token=token)
        origin    = getattr(settings, 'FRONTEND_URL', 'https://metamorphose.vercel.app')
        reset_url = f"{origin}/reset-password?token={token}"
        send_mail(
            subject="Réinitialisation de votre mot de passe — Méta'Morph'Ose",
            message=(
                f"Bonjour {user.first_name or user.email},\n\n"
                f"Cliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_url}\n\n"
                "Ce lien est valable 1 heure.\n\n"
                "Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
                "Prélia Apedo — Méta'Morph'Ose"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
        PasswordResetToken.purge_expired()
    except User.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Erreur demander_reset pour {email} : {e}")
    return Response({"detail": "Si cet email existe, un lien de réinitialisation a été envoyé."})


@api_view(["POST"])
@permission_classes([AllowAny])
def confirmer_reset(request):
    token    = request.data.get("token", "").strip()
    password = request.data.get("password", "")
    if not token or not password:
        return Response({"detail": "Token et mot de passe requis."}, status=400)
    if len(password) < 8:
        return Response({"detail": "8 caractères minimum."}, status=400)
    try:
        token_obj = PasswordResetToken.objects.select_related('user').get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response({"detail": "Lien invalide ou expiré."}, status=400)
    if not token_obj.is_valid():
        return Response({"detail": "Lien invalide ou expiré."}, status=400)
    try:
        user = token_obj.user
        user.set_password(password)
        user.save()
        token_obj.used = True
        token_obj.save(update_fields=['used'])
        return Response({"detail": "Mot de passe réinitialisé avec succès."})
    except Exception as e:
        logger.error(f"Erreur confirmer_reset : {e}")
        return Response({"detail": "Erreur lors de la réinitialisation."}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generer_certificat(request):
    from django.http import HttpResponse
    from io import BytesIO
    from datetime import date
    user = request.user
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
        buffer = BytesIO()
        w, h   = A4
        c      = canvas.Canvas(buffer, pagesize=A4)
        c.setFillColor(HexColor('#0A0A0A'))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(2)
        c.rect(30, 30, w-60, h-60, fill=0, stroke=1)
        c.setLineWidth(0.5)
        c.rect(38, 38, w-76, h-76, fill=0, stroke=1)
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawCentredString(w/2, h-60, "✦  ✦  ✦")
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w/2, h-90, "MÉTA'MORPH'OSE")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)
        c.drawCentredString(w/2, h-108, "Programme de Transformation Féminine")
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(1)
        c.line(80, h-122, w-80, h-122)
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-155, "Ce certificat est décerné à")
        nom = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
        # Adapter la taille de police si le nom est long
        nom_font_size = 28 if len(nom) <= 22 else (22 if len(nom) <= 30 else 16)
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Bold", nom_font_size)
        c.drawCentredString(w/2, h-200, nom[:40])  # tronquer à 40 chars max
        c.setStrokeColor(HexColor('#C2185B'))
        c.setLineWidth(1.5)
        c.line(100, h-215, w-100, h-215)
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-245, "pour avoir complété avec succès le programme")
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w/2, h-270, "MÉTA'MORPH'OSE — 8 Semaines")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-295, "De l'ombre à la lumière")
        formules      = {'F1':'Live · Groupe','F2':'Live · Privé','F3':'Présentiel · Groupe','F4':'Présentiel · Privé'}
        formule_label = formules.get(user.formule, user.formule or "")
        if formule_label:
            c.setFillColor(HexColor('#C2185B'))
            c.setFont("Helvetica", 9)
            c.drawCentredString(w/2, h-315, f"Formule : {formule_label}")
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(w/2, h-355, "« Je ne crée pas des apparences.")
        c.drawCentredString(w/2, h-370, "Je révèle des essences. »")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)
        c.drawCentredString(w/2, h-390, "— Prélia Apedo")
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(0.5)
        c.line(80, h-415, w-80, h-415)
        aujourd_hui = date.today().strftime("%d %B %Y")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)
        c.drawString(80, h-445, f"Date : {aujourd_hui}")
        c.drawRightString(w-80, h-445, "Prélia Apedo")
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawRightString(w-80, h-458, "Fondatrice · White & Black · Méta'Morph'Ose")
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawCentredString(w/2, 55, "✦  ✦  ✦")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 7)
        c.drawCentredString(w/2, 44, "White & Black — Bénin, Afrique")
        c.save()
        buffer.seek(0)
        nom_fichier = f"Certificat_MetaMorphOse_{nom.replace(' ','_')}.pdf"
        response    = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
        return response
    except ImportError:
        return Response({"detail": "ReportLab non installé."}, status=500)


def _email_bienvenue(user):
    formule_labels = {'F1':'Live · Groupe','F2':'Live · Privé','F3':'Présentiel · Groupe','F4':'Présentiel · Privé'}
    formule_label  = formule_labels.get(user.formule, 'Non définie')
    send_mail(
        subject="Bienvenue dans Méta'Morph'Ose !",
        message=(
            f"Bonjour {user.first_name or user.email},\n\n"
            f"Votre inscription (formule {formule_label}) a bien été reçue.\n\n"
            "Prélia vous contactera sous 24 à 48h.\n\n"
            f"Connectez-vous : {settings.FRONTEND_URL}/espace-membre\n\n"
            "Prélia Apedo — Méta'Morph'Ose"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
