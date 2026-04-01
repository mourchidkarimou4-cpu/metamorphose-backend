from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    if s.is_valid():
        user = s.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email','')
    password = request.data.get('password','')
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            })
        return Response({'detail': 'Mot de passe incorrect.'}, status=400)
    except User.DoesNotExist:
        return Response({'detail': 'Aucun compte avec cet email.'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)

@api_view(['POST'])
@permission_classes([AllowAny])
def contact(request):
    from contenu.models import DemandeContact
    DemandeContact.objects.create(
        prenom=request.data.get('prenom',''),
        nom=request.data.get('nom',''),
        email=request.data.get('email',''),
        whatsapp=request.data.get('whatsapp',''),
        pays=request.data.get('pays',''),
        formule=request.data.get('formule',''),
        message=request.data.get('message',''),
    )
    return Response({'detail': 'Demande reçue.'}, status=201)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    email     = request.data.get("email", user.email)
    firstName = request.data.get("first_name", user.first_name)
    lastName  = request.data.get("last_name", user.last_name)
    whatsapp  = request.data.get("whatsapp", user.whatsapp)
    
    # Vérifier email unique
    from accounts.models import CustomUser
    if CustomUser.objects.exclude(pk=user.pk).filter(email=email).exists():
        return Response({"detail": "Cet email est déjà utilisé."}, status=400)
    
    user.email      = email
    user.first_name = firstName
    user.last_name  = lastName
    user.whatsapp   = whatsapp or user.whatsapp
    user.save()
    return Response({
        "email": user.email, "first_name": user.first_name,
        "last_name": user.last_name, "whatsapp": user.whatsapp,
        "is_staff": user.is_staff
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user        = request.user
    old_password= request.data.get("old_password", "")
    new_password= request.data.get("new_password", "")
    if not user.check_password(old_password):
        return Response({"detail": "Ancien mot de passe incorrect."}, status=400)
    if len(new_password) < 8:
        return Response({"detail": "Le mot de passe doit contenir au moins 8 caractères."}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({"detail": "Mot de passe modifié avec succès."})

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    email     = request.data.get("email", user.email)
    firstName = request.data.get("first_name", user.first_name)
    lastName  = request.data.get("last_name", user.last_name)
    whatsapp  = request.data.get("whatsapp", user.whatsapp)
    
    # Vérifier email unique
    from accounts.models import CustomUser
    if CustomUser.objects.exclude(pk=user.pk).filter(email=email).exists():
        return Response({"detail": "Cet email est déjà utilisé."}, status=400)
    
    user.email      = email
    user.first_name = firstName
    user.last_name  = lastName
    user.whatsapp   = whatsapp or user.whatsapp
    user.save()
    return Response({
        "email": user.email, "first_name": user.first_name,
        "last_name": user.last_name, "whatsapp": user.whatsapp,
        "is_staff": user.is_staff
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user        = request.user
    old_password= request.data.get("old_password", "")
    new_password= request.data.get("new_password", "")
    if not user.check_password(old_password):
        return Response({"detail": "Ancien mot de passe incorrect."}, status=400)
    if len(new_password) < 8:
        return Response({"detail": "Le mot de passe doit contenir au moins 8 caractères."}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({"detail": "Mot de passe modifié avec succès."})

import secrets
from django.core.mail import send_mail
from django.conf import settings

# Stockage temporaire des tokens (en prod utiliser Redis ou DB)
_reset_tokens = {}

@api_view(["POST"])
@permission_classes([AllowAny])
def demander_reset(request):
    email = request.data.get("email","").strip()
    try:
        from accounts.models import CustomUser
        user = CustomUser.objects.get(email=email)
        token = secrets.token_urlsafe(32)
        _reset_tokens[token] = user.pk
        reset_url = f"{request.data.get('origin','http://localhost:5173')}/reset-password?token={token}"
        send_mail(
            subject="Réinitialisation de votre mot de passe — Méta'Morph'Ose",
            message=f"Bonjour {user.first_name or user.email},\n\nCliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_url}\n\nCe lien est valable 1 heure.\n\nSi vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\nPrélia Apedo — Méta'Morph'Ose",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass
    # Toujours répondre OK pour ne pas révéler si l'email existe
    return Response({"detail": "Si cet email existe, un lien de réinitialisation a été envoyé."})

@api_view(["POST"])
@permission_classes([AllowAny])
def confirmer_reset(request):
    token    = request.data.get("token","")
    password = request.data.get("password","")
    if not token or not password:
        return Response({"detail":"Token et mot de passe requis."}, status=400)
    if len(password) < 8:
        return Response({"detail":"8 caractères minimum."}, status=400)
    user_pk = _reset_tokens.get(token)
    if not user_pk:
        return Response({"detail":"Lien invalide ou expiré."}, status=400)
    try:
        from accounts.models import CustomUser
        user = CustomUser.objects.get(pk=user_pk)
        user.set_password(password)
        user.save()
        del _reset_tokens[token]
        return Response({"detail":"Mot de passe réinitialisé avec succès."})
    except Exception:
        return Response({"detail":"Erreur lors de la réinitialisation."}, status=500)
# accounts/views.py — Ajouter cette vue pour le certificat PDF

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generer_certificat(request):
    """Génère un certificat PDF pour la membre connectée"""
    from django.http import HttpResponse
    from io import BytesIO
    import textwrap
    from datetime import date

    user = request.user

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = BytesIO()
        w, h = A4
        c = canvas.Canvas(buffer, pagesize=A4)

        # Fond noir
        c.setFillColor(HexColor('#0A0A0A'))
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # Bordure dorée
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(2)
        c.rect(30, 30, w-60, h-60, fill=0, stroke=1)
        c.setLineWidth(0.5)
        c.rect(38, 38, w-76, h-76, fill=0, stroke=1)

        # Ornement haut
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawCentredString(w/2, h-60, "✦  ✦  ✦")

        # Titre
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w/2, h-90, "MÉTA'MORPH'OSE")

        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)
        c.drawCentredString(w/2, h-108, "Programme de Transformation Féminine")

        # Ligne dorée
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(1)
        c.line(80, h-122, w-80, h-122)

        # Certificat de
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-155, "Ce certificat est décerné à")

        # Nom de la participante
        nom = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w/2, h-200, nom)

        # Ligne sous le nom
        c.setStrokeColor(HexColor('#C2185B'))
        c.setLineWidth(1.5)
        c.line(100, h-215, w-100, h-215)

        # Texte certificat
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-245, "pour avoir complété avec succès le programme")

        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w/2, h-270, "MÉTA'MORPH'OSE — 8 Semaines")

        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, h-295, "De l'ombre à la lumière")

        # Formule
        formules = {'F1':'Live · Groupe','F2':'Live · Privé','F3':'Présentiel · Groupe','F4':'Présentiel · Privé'}
        formule_label = formules.get(user.formule, user.formule or "")
        if formule_label:
            c.setFillColor(HexColor('#C2185B'))
            c.setFont("Helvetica", 9)
            c.drawCentredString(w/2, h-315, f"Formule : {formule_label}")

        # Citation
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(w/2, h-355, "« Je ne crée pas des apparences.")
        c.drawCentredString(w/2, h-370, "Je révèle des essences. »")

        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)
        c.drawCentredString(w/2, h-390, "— Prélia Apedo")

        # Ligne séparation
        c.setStrokeColor(HexColor('#C9A96A'))
        c.setLineWidth(0.5)
        c.line(80, h-415, w-80, h-415)

        # Date et signature
        aujourd_hui = date.today().strftime("%d %B %Y")
        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 9)

        # Côté gauche — date
        c.drawString(80, h-445, f"Date : {aujourd_hui}")

        # Côté droit — signature
        c.drawRightString(w-80, h-445, "Prélia Apedo")
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawRightString(w-80, h-458, "Fondatrice · White & Black · Méta'Morph'Ose")

        # Ornement bas
        c.setFillColor(HexColor('#C9A96A'))
        c.setFont("Helvetica", 8)
        c.drawCentredString(w/2, 55, "✦  ✦  ✦")

        c.setFillColor(HexColor('#F8F5F2'))
        c.setFont("Helvetica", 7)
        c.drawCentredString(w/2, 44, "White & Black — Bénin, Afrique")

        c.save()
        buffer.seek(0)

        nom_fichier = f"Certificat_MetaMorphOse_{nom.replace(' ','_')}.pdf"
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
        return response

    except ImportError:
        return Response({"detail": "ReportLab non installé. Installez avec: pip install reportlab"}, status=500)
