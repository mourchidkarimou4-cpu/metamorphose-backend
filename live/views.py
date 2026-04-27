from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from .models import Salle, Participant, Message
import uuid, random, string, os

def generer_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ── CRÉER UNE SALLE ──────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_salle(request):
    code = request.data.get('code_acces', '').strip().upper() or generer_code()
    room_name = f"mmo-{uuid.uuid4().hex[:12]}"
    salle = Salle.objects.create(
        titre=request.data.get('titre', 'Masterclass'),
        description=request.data.get('description', ''),
        hote=request.user,
        code_acces=code,
        mode=request.data.get('mode', 'live'),
        max_participants=request.data.get('max_participants', 1000),
        daily_room_name=room_name,  # on réutilise ce champ pour livekit_room_name
    )
    # Token hôte
    token = generer_token_livekit(
        room_name=room_name,
        identity=str(request.user.id),
        nom=request.user.get_full_name() or request.user.email,
        is_host=True
    )
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'code_acces': salle.code_acces,
        'room_name': room_name,
        'livekit_url': LIVEKIT_URL,
        'token': token,
        'statut': salle.statut,
    })

# ── MES SALLES ───────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_salles(request):
    salles = Salle.objects.filter(hote=request.user).order_by('-created_at')
    data = [{
        'id': str(s.id),
        'titre': s.titre,
        'code_acces': s.code_acces,
        'statut': s.statut,
        'mode': s.mode,
        'room_name': s.daily_room_name,
        'created_at': s.created_at.strftime('%d/%m/%Y %H:%M'),
        'nb_participants': s.participants.count(),
    } for s in salles]
    return Response(data)

# ── SALLES ACTIVES ───────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def salles_actives(request):
    salles = Salle.objects.filter(statut__in=['attente', 'active']).order_by('-created_at')
    data = [{
        'id': str(s.id),
        'titre': s.titre,
        'description': s.description,
        'statut': s.statut,
        'mode': s.mode,
        'created_at': s.created_at.strftime('%d/%m/%Y %H:%M'),
    } for s in salles]
    return Response(data)

# ── INFOS SALLE ──────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def infos_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'description': salle.description,
        'statut': salle.statut,
        'mode': salle.mode,
        'created_at': salle.created_at.strftime('%d/%m/%Y %H:%M'),
    })

# ── REJOINDRE (HÔTE) ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rejoindre_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)
    is_host = salle.hote == request.user
    token = generer_token_livekit(
        room_name=salle.daily_room_name,
        identity=str(request.user.id),
        nom=request.user.get_full_name() or request.user.email,
        is_host=is_host
    )
    return Response({
        'livekit_url': LIVEKIT_URL,
        'token': token,
        'room_name': salle.daily_room_name,
        'is_host': is_host,
    })

# ── REJOINDRE PUBLIC (email + code) ─────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def rejoindre_live_public(request, room_id):
    email = request.data.get('email', '').strip().lower()
    code  = request.data.get('code', '').strip().upper()
    nom   = request.data.get('nom', email)

    if not email or not code:
        return Response({'error': 'Email et code requis'}, status=400)

    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)

    if salle.code_acces and salle.code_acces.upper() != code:
        return Response({'error': 'Code incorrect'}, status=403)

    if salle.statut == 'terminee':
        return Response({'error': 'Ce live est terminé'}, status=403)

    token = generer_token_livekit(
        room_name=salle.daily_room_name,
        identity=email,
        nom=nom,
        is_host=False
    )

    Participant.objects.get_or_create(
        salle=salle,
        nom=nom,
        defaults={'role': 'spectateur'}
    )

    return Response({
        'livekit_url': LIVEKIT_URL,
        'token': token,
        'room_name': salle.daily_room_name,
        'titre': salle.titre,
    })

# ── TOKEN LIVEKIT (hôte depuis dashboard) ───────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def livekit_token(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)
    token = generer_token_livekit(
        room_name=salle.daily_room_name,
        identity=str(request.user.id),
        nom=request.user.get_full_name() or request.user.email,
        is_host=True
    )
    return Response({'token': token, 'livekit_url': LIVEKIT_URL, 'room_name': salle.daily_room_name})

# ── TERMINER SALLE ───────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminer_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id, hote=request.user)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)
    salle.statut = 'terminee'
    salle.ended_at = timezone.now()
    salle.save()
    return Response({'status': 'terminee'})

# ── MODIFIER SALLE ───────────────────────────────────────────────────────────
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def modifier_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id, hote=request.user)
    except Salle.DoesNotExist:
        return Response({'error': 'Salle non trouvée'}, status=404)
    for field in ['titre', 'description', 'statut', 'mode', 'max_participants']:
        if field in request.data:
            setattr(salle, field, request.data[field])
    salle.save()
    return Response({'status': 'ok'})

# ── STUBS (compatibilité) ─────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_peer(request, room_id):
    return Response({'status': 'ok'})

@api_view(['GET'])
@permission_classes([AllowAny])
def list_peers(request, room_id):
    return Response([])

@api_view(['POST'])
@permission_classes([AllowAny])
def leave_peer(request, room_id):
    return Response({'status': 'ok'})

@api_view(['GET'])
@permission_classes([AllowAny])
def daily_token(request, room_id):
    return Response({'error': 'Daily.co remplacé par LiveKit'}, status=410)
