from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from .models import Salle, Participant, Message
import uuid
import requests as http_requests

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_salle(request):
    code = request.data.get('mot_de_passe', '').strip() or request.data.get('code_acces', '').strip()
    salle = Salle.objects.create(
        titre=request.data.get('titre', 'Ma réunion'),
        description=request.data.get('description', ''),
        hote=request.user,
        code_acces=code.upper() if code else '',
        mode=request.data.get('mode', 'live'),
        max_participants=request.data.get('max_participants', 1000),
        lien_zoom=request.data.get('lien_zoom', ''),
    )

    # Créer la room Daily.co
    daily_api_key = getattr(settings, 'DAILY_API_KEY', '')
    daily_room_name = ''
    if daily_api_key:
        try:
            resp = http_requests.post(
                'https://api.daily.co/v1/rooms',
                headers={
                    'Authorization': f'Bearer {daily_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'name': str(salle.id).replace('-', ''),
                    'properties': {
                        'enable_chat': True,
                        'enable_screenshare': True,
                        'enable_recording': 'cloud',
                        'start_video_off': False,
                        'start_audio_off': False,
                        'exp': int(timezone.now().timestamp()) + 86400,
                    }
                },
                timeout=10
            )
            if resp.status_code in [200, 201]:
                daily_room_name = resp.json().get('name', '')
                salle.daily_room_name = daily_room_name
                salle.save()
        except Exception:
            pass

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://metamorphose-frontend.vercel.app')
    lien = f"{frontend_url}/meeting/{str(salle.id)}"
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'mode': salle.mode,
        'code_acces': salle.code_acces,
        'lien': lien,
        'statut': salle.statut,
        'daily_room_name': daily_room_name,
        'lien_zoom': salle.lien_zoom,
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
        'protege': bool(salle.code_acces),
        'lien_zoom': salle.lien_zoom,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def rejoindre_salle(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)

    if salle.code_acces and request.data.get('code_acces', '').strip().upper() != salle.code_acces.upper():
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
        'protege': bool(s.code_acces),
        'lien_zoom': s.lien_zoom,
        'started_at': s.started_at,
        'created_at': s.created_at,
    } for s in salles])


# ── Registre PeerJS (via DB) ────────────────────────────────────
from .models import PeerActif

@api_view(['POST'])
@permission_classes([AllowAny])
def register_peer(request, room_id):
    peer_id = request.data.get('peer_id')
    nom = request.data.get('nom', 'Anonyme')
    if not peer_id:
        return Response({'detail': 'peer_id requis.'}, status=400)
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)
    PeerActif.objects.update_or_create(peer_id=peer_id, defaults={'salle': salle, 'nom': nom})
    return Response({'ok': True})

@api_view(['GET'])
@permission_classes([AllowAny])
def list_peers(request, room_id):
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'peers': []})
    peers = PeerActif.objects.filter(salle=salle).values('peer_id', 'nom')
    return Response({'peers': list(peers)})

@api_view(['POST'])
@permission_classes([AllowAny])
def leave_peer(request, room_id):
    peer_id = request.data.get('peer_id')
    if not peer_id:
        return Response({'detail': 'peer_id requis.'}, status=400)
    PeerActif.objects.filter(peer_id=peer_id).delete()
    return Response({'ok': True})

import random, string

def generer_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@api_view(['POST'])
@permission_classes([AllowAny])
def rejoindre_live_public(request, room_id):
    """Accès public au live via email + code."""
    email = request.data.get('email', '').strip()
    code  = request.data.get('code', '').strip().upper()
    if not email or not code:
        return Response({'detail': 'Email et code requis.'}, status=400)
    try:
        salle = Salle.objects.get(id=room_id, statut='active')
    except Salle.DoesNotExist:
        return Response({'detail': 'Live introuvable ou terminé.'}, status=404)
    if salle.code_acces and salle.code_acces.upper() != code:
        return Response({'detail': 'Code incorrect.'}, status=403)
    # Enregistrer le participant
    Participant.objects.get_or_create(
        salle=salle, nom=email,
        defaults={'role': 'spectateur'}
    )
    return Response({
        'room_id': str(salle.id),
        'titre':   salle.titre,
        'email':   email,
    })



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def modifier_salle(request, room_id):
    """Modifier une salle — notamment le lien Zoom."""
    try:
        salle = Salle.objects.get(id=room_id, hote=request.user)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)

    for field in ['titre', 'description', 'lien_zoom', 'code_acces', 'mode']:
        if field in request.data:
            setattr(salle, field, request.data[field])
    salle.save()
    return Response({
        'id': str(salle.id),
        'titre': salle.titre,
        'lien_zoom': salle.lien_zoom,
        'statut': salle.statut,
    })

# ── Daily.co — Générer token de meeting ───────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def daily_token(request, room_id):
    """Génère un token Daily.co pour rejoindre une salle."""
    try:
        salle = Salle.objects.get(id=room_id)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)

    daily_api_key = getattr(settings, 'DAILY_API_KEY', '')
    if not daily_api_key:
        return Response({'detail': 'Daily.co non configuré.'}, status=500)

    is_owner = salle.hote == request.user
    is_admin = request.user.is_staff

    try:
        room_name = salle.daily_room_name or str(salle.id).replace('-', '')

        # Créer la room Daily si elle n'existe pas encore
        if not salle.daily_room_name:
            create_resp = http_requests.post(
                'https://api.daily.co/v1/rooms',
                headers={
                    'Authorization': f'Bearer {daily_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'name': room_name,
                    'properties': {
                        'enable_chat': True,
                        'enable_screenshare': True,
                        'exp': int(timezone.now().timestamp()) + 86400,
                    }
                },
                timeout=10
            )
            if create_resp.status_code in [200, 201]:
                room_name = create_resp.json().get('name', room_name)
                salle.daily_room_name = room_name
                salle.save()

        # Générer le token de meeting
        resp = http_requests.post(
            'https://api.daily.co/v1/meeting-tokens',
            headers={
                'Authorization': f'Bearer {daily_api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'properties': {
                    'room_name': room_name,
                    'user_name': request.user.first_name or request.user.email,
                    'is_owner': is_owner or is_admin,

                    'start_video_off': False,
                    'start_audio_off': False,
                    'exp': int(timezone.now().timestamp()) + 7200,
                }
            },
            timeout=10
        )
        if resp.status_code in [200, 201]:
            token = resp.json().get('token', '')
            room_url = f"https://masterclass-ose-live.daily.co/{room_name}"
            return Response({
                'token': token,
                'room_url': room_url,
                'room_name': room_name,
                'is_owner': is_owner or is_admin,
            })
        return Response({'detail': f'Erreur Daily.co: {resp.text}'}, status=500)
    except Exception as e:
        return Response({'detail': str(e)}, status=500)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def maj_lien_zoom(request, room_id):
    """Mettre à jour le lien Zoom d'une salle."""
    try:
        salle = Salle.objects.get(id=room_id, hote=request.user)
    except Salle.DoesNotExist:
        return Response({'detail': 'Salle introuvable.'}, status=404)
    salle.lien_zoom = request.data.get('lien_zoom', '')
    salle.save()
    return Response({'lien_zoom': salle.lien_zoom})
