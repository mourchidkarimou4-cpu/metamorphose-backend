from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import Guide, Replay, Abonne
from .serializers import GuideSerializer, ReplaySerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def guides(request):
    data = Guide.objects.filter(actif=True).order_by('numero')
    return Response(GuideSerializer(data, many=True, context={'request':request}).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def replays(request):
    formule = request.user.formule
    if not formule:
        return Response([])
    data = Replay.objects.filter(actif=True, formules__contains=formule).order_by('semaine')
    return Response(ReplaySerializer(data, many=True).data)



@api_view(['POST'])
@permission_classes([AllowAny])
def abonner_newsletter(request):
    from contenu.models import Abonne
    from django.core.mail import send_mail
    from django.conf import settings

    email  = request.data.get('email', '').strip().lower()
    prenom = request.data.get('prenom', '').strip()

    if not email:
        return Response({'detail': 'Email requis.'}, status=400)

    if Abonne.objects.filter(email=email, actif=True).exists():
        return Response({'detail': 'Vous êtes déjà abonné(e).'}, status=400)

    Abonne.objects.update_or_create(
        email=email,
        defaults={'prenom': prenom, 'actif': True}
    )

    # Email de confirmation
    try:
        send_mail(
            subject="Bienvenue dans l'univers Méta'Morph'Ose ✦",
            message=(
                f"Bonjour{' ' + prenom if prenom else ''},\n\n"
                "Merci de rejoindre la communauté Méta'Morph'Ose.\n\n"
                "Vous recevrez nos actualités, conseils et invitations exclusives.\n\n"
                "Prélia Apedo — Méta'Morph'Ose"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass

    return Response({'detail': 'Inscription confirmée. Merci !'}, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def se_desabonner(request):
    from contenu.models import Abonne
    email = request.query_params.get('email', '').strip().lower()
    if email:
        Abonne.objects.filter(email=email).update(actif=False)
    return Response({'detail': 'Vous avez été désabonné(e).'})

@api_view(['POST'])
@permission_classes([AllowAny])
def acceder_replay(request, replay_id):
    """Accès à un replay via email + code."""
    from .models import Replay
    email = request.data.get('email', '').strip()
    code  = request.data.get('code', '').strip().upper()
    if not email or not code:
        return Response({'detail': 'Email et code requis.'}, status=400)
    try:
        replay = Replay.objects.get(id=replay_id, actif=True)
    except Replay.DoesNotExist:
        return Response({'detail': 'Replay introuvable.'}, status=404)
    if not replay.code_acces or replay.code_acces.upper() != code:
        return Response({'detail': 'Code incorrect.'}, status=403)
    from .serializers import ReplaySerializer
    return Response({
        'acces': True,
        'replay': ReplaySerializer(replay).data,
        'email': email,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def infos_replay_public(request, replay_id):
    """Infos publiques d'un replay (titre, sans contenu)."""
    from .models import Replay
    try:
        replay = Replay.objects.get(id=replay_id, actif=True)
    except Replay.DoesNotExist:
        return Response({'detail': 'Replay introuvable.'}, status=404)
    return Response({
        'id': replay.id,
        'titre': replay.titre,
        'semaine': replay.semaine,
        'a_code': bool(replay.code_acces),
    })
