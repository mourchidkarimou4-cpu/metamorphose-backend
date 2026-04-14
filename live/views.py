from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from .models import Salle, Participant, Message
import uuid

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_salle(request):
    salle = Salle.objects.create(
        titre=request.data.get('titre', 'Ma réunion'),
        description=request.data.get('description', ''),
        hote=request.user,
        mot_de_passe=request.data.get('mot_de_passe', ''),
        mode=request.data.get('mode', 'reunion'),
        max_participants=request.data.get('max_participants', 1000),
    )
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'mode': salle.mode,
        'mot_de_passe': salle.mot_de_passe,
        'statut': salle.statut,
        'created_at': salle.created_at,
    }, status=201)

@api_view(['GET'])
@permission_classes([AllowAny])
def infos_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'mode': salle.mode,
        'statut': salle.statut,
        'hote': salle.hote.first_name or salle.hote.email,
        'participants': salle.participants.filter(quitte_at__isnull=True).count(),
        'max_participants': salle.max_participants,
        'protege': bool(salle.mot_de_passe),
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def rejoindre_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)

    if salle.mot_de_passe and request.data.get('mot_de_passe') != salle.mot_de_passe:
        return Response({'detail': 'Mot de passe incorrect.'}, status=403)

    if salle.statut == 'terminee':
        return Response({'detail': 'Cette réunion est terminée.'}, status=403)

    nom = request.data.get('nom', 'Anonyme')
    role = 'participant'
    if request.user.is_authenticated and str(salle.hote.id) == str(request.user.id):
        role = 'hote'
        if salle.statut == 'attente':
            salle.statut = 'active'
            salle.started_at = timezone.now()
            salle.save()

    Participant.objects.create(salle=salle, user=request.user if request.user.is_authenticated else None, nom=nom, role=role)

    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'mode': salle.mode,
        'role': role,
        'peer_id': str(uuid.uuid4()),
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminer_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id, hote=request.user)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable ou non autorisé.'}, status=404)
    salle.statut = 'terminee'
    salle.ended_at = timezone.now()
    salle.save()
    return Response({'detail': 'Réunion terminée.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_salles(request):
    salles = Salle.objects.filter(hote=request.user).order_by('-created_at')[:20]
    return Response([{
        'id': str(s.id),
        'titre': s.titre,
        'mode': s.mode,
        'statut': s.statut,
        'created_at': s.created_at,
        'participants': s.participants.count(),
    } for s in salles])

@api_view(['GET'])
@permission_classes([AllowAny])
def salles_actives(request):
    """Liste publique des salles en cours ou en attente."""
    salles = Salle.objects.filter(statut__in=['active', 'attente']).order_by('-created_at')[:20]
    return Response([{
        'id': str(s.id),
        'titre': s.titre,
        'description': s.description,
        'mode': s.mode,
        'statut': s.statut,
        'hote_nom': s.hote.first_name or s.hote.email,
        'participants_count': s.participants.filter(quitte_at__isnull=True).count(),
        'mot_de_passe': bool(s.mot_de_passe),
        'started_at': s.started_at,
        'created_at': s.created_at,
    } for s in salles])

# ── Registre PeerJS (remplace WebSocket pour le signaling) ──────

from django.core.cache import cache

@api_view(['POST'])
@permission_classes([AllowAny])
def register_peer(request, room_id):
    """Enregistrer un peer_id dans la salle."""
    peer_id = request.data.get('peer_id')
    nom = request.data.get('nom', 'Anonyme')
    if not peer_id:
        return Response({'detail': 'peer_id requis.'}, status=400)
    key = f'live_peers_{room_id}'
    peers = cache.get(key, [])
    peers = [p for p in peers if p['peer_id'] != peer_id]
    peers.append({'peer_id': peer_id, 'nom': nom})
    cache.set(key, peers, timeout=3600)
    return Response({'ok': True})

@api_view(['GET'])
@permission_classes([AllowAny])
def list_peers(request, room_id):
    """Lister les peers actifs dans une salle."""
    key = f'live_peers_{room_id}'
    peers = cache.get(key, [])
    return Response({'peers': peers})

@api_view(['POST'])
@permission_classes([AllowAny])
def leave_peer(request, room_id):
    """Retirer un peer de la salle."""
    peer_id = request.data.get('peer_id')
    if not peer_id:
        return Response({'detail': 'peer_id requis.'}, status=400)
    key = f'live_peers_{room_id}'
    peers = cache.get(key, [])
    peers = [p for p in peers if p['peer_id'] != peer_id]
    cache.set(key, peers, timeout=3600)
    return Response({'ok': True})
