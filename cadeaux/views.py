from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import CartesCadeaux
from .serializers import CartePublicSerializer, CarteCommandeSerializer, CarteAdminSerializer

# ── PUBLIC ──────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def commander_carte(request):
    """Créer une commande de carte cadeau"""
    s = CarteCommandeSerializer(data=request.data)
    if s.is_valid():
        from datetime import date, timedelta
        carte = s.save()
        # Expiration 1 an
        carte.date_expiration = date.today() + timedelta(days=365)
        carte.save()

        # Email de confirmation à l'acheteur
        try:
            formule_label = dict(CartesCadeaux.FORMULES).get(carte.formule, carte.formule)
            send_mail(
                subject=f"Votre carte cadeau Méta'Morph'Ose — {carte.code}",
                message=(
                    f"Bonjour {carte.acheteur_nom},\n\n"
                    f"Votre commande de carte cadeau a bien été reçue.\n\n"
                    f"Formule : {formule_label}\n"
                    f"Pour : {carte.destinataire_nom}\n"
                    f"Code : {carte.code}\n\n"
                    f"Prélia vous contactera sous 24h pour finaliser le paiement "
                    f"et activer la carte.\n\n"
                    f"Méta'Morph'Ose · White & Black"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[carte.acheteur_email],
                fail_silently=True,
            )
        except Exception:
            pass

        return Response({
            'code':    carte.code,
            'message': 'Votre commande est enregistrée. Prélia vous contactera sous 24h.',
            'carte':   CartePublicSerializer(carte).data,
        }, status=201)
    return Response(s.errors, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def verifier_carte(request, code):
    """Vérifier la validité d'une carte cadeau"""
    try:
        carte = CartesCadeaux.objects.get(code=code.upper())
        data  = CartePublicSerializer(carte).data
        data['valide'] = carte.statut == 'payee'
        return Response(data)
    except CartesCadeaux.DoesNotExist:
        return Response({'detail':'Code invalide.','valide':False}, status=404)

# ── ADMIN ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_cartes(request):
    qs = CartesCadeaux.objects.all()
    return Response(CarteAdminSerializer(qs, many=True).data)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def modifier_carte(request, pk):
    try:
        carte = CartesCadeaux.objects.get(pk=pk)
    except CartesCadeaux.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)
    s = CarteAdminSerializer(carte, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def activer_carte(request, pk):
    """Marquer une carte comme payée"""
    try:
        carte = CartesCadeaux.objects.get(pk=pk)
        carte.statut = 'payee'
        carte.save()
        return Response({'detail':'Carte activée.', 'code': carte.code})
    except CartesCadeaux.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def utiliser_carte(request, pk):
    """Marquer une carte comme utilisée"""
    try:
        carte = CartesCadeaux.objects.get(pk=pk)
        carte.statut          = 'utilisee'
        carte.date_utilisation= timezone.now()
        carte.utilisee_par    = request.data.get('email','')
        carte.save()
        return Response({'detail':'Carte marquée comme utilisée.'})
    except CartesCadeaux.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)
