import hmac
import hashlib
import time
import base64
import os
import requests as http_requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from .models import ReunionZoom

ZOOM_ACCOUNT_ID    = os.environ.get('ZOOM_ACCOUNT_ID', '')
ZOOM_S2S_CLIENT_ID     = os.environ.get('ZOOM_S2S_CLIENT_ID', '')
ZOOM_S2S_CLIENT_SECRET = os.environ.get('ZOOM_S2S_CLIENT_SECRET', '')

def get_zoom_token():
    """Obtenir un token OAuth Zoom Server-to-Server"""
    credentials = base64.b64encode(f"{ZOOM_S2S_CLIENT_ID}:{ZOOM_S2S_CLIENT_SECRET}".encode()).decode()
    response = http_requests.post(
        f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ZOOM_ACCOUNT_ID}",
        headers={"Authorization": f"Basic {credentials}"}
    )
    return response.json().get('access_token', '')

def generer_signature(meeting_number, role):
    """Générer la signature JWT pour le SDK Zoom Meeting via PyJWT"""
    import jwt
    iat = int(time.time()) - 30
    exp = iat + 60 * 60 * 2

    payload = {
        "appKey": ZOOM_SDK_CLIENT_ID,
        "sdkKey": ZOOM_SDK_CLIENT_ID,
        "mn": str(meeting_number),
        "role": int(role),
        "iat": iat,
        "exp": exp,
        "tokenExp": exp
    }

    signature = jwt.encode(payload, ZOOM_S2S_CLIENT_SECRET, algorithm="HS256")
    if isinstance(signature, bytes):
        return signature.decode('utf-8')
    return signature

# ── CRÉER UNE RÉUNION ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_reunion(request):
    titre      = request.data.get('titre', 'Masterclass Méta\'Morph\'Ose')
    description = request.data.get('description', '')
    duree      = request.data.get('duree', 60)
    date_debut = request.data.get('date_debut', None)

    token = get_zoom_token()
    if not token:
        return Response({'error': 'Impossible d\'obtenir le token Zoom'}, status=500)

    payload = {
        'topic': titre,
        'type': 1,  # 1 = instant, 2 = scheduled
        'duration': duree,
        'password': '',
        'settings': {
            'host_video': True,
            'participant_video': True,
            'join_before_host': False,
            'mute_upon_entry': True,
            'waiting_room': True,
            'allow_multiple_devices': True,
            'auto_recording': 'none',
        }
    }

    if date_debut:
        payload['type'] = 2
        payload['start_time'] = date_debut

    resp = http_requests.post(
        'https://api.zoom.us/v2/users/me/meetings',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json=payload
    )
    data = resp.json()

    if resp.status_code != 201:
        return Response({'error': data.get('message', 'Erreur Zoom')}, status=400)

    reunion = ReunionZoom.objects.create(
        titre=titre,
        description=description,
        meeting_id=str(data['id']),
        password=data.get('password', ''),
        join_url=data.get('join_url', ''),
        start_url=data.get('start_url', ''),
        hote=request.user,
        duree=duree,
    )

    return Response({
        'id': reunion.id,
        'titre': reunion.titre,
        'meeting_id': reunion.meeting_id,
        'password': reunion.password,
        'join_url': reunion.join_url,
        'start_url': reunion.start_url,
    })

# ── SIGNATURE SDK ────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def get_signature(request):
    meeting_number = request.data.get('meeting_number', '')
    role = int(request.data.get('role', 0))  # 0=participant, 1=hôte

    if not meeting_number:
        return Response({'error': 'meeting_number requis'}, status=400)

    signature = generer_signature(meeting_number, role)
    return Response({
        'signature': signature,
        'sdk_key': ZOOM_S2S_CLIENT_ID,
    })

# ── LISTE RÉUNIONS ───────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def liste_reunions(request):
    reunions = ReunionZoom.objects.filter(statut__in=['attente', 'active']).order_by('-created_at')
    data = [{
        'id': r.id,
        'titre': r.titre,
        'meeting_id': r.meeting_id,
        'password': r.password,
        'statut': r.statut,
        'created_at': r.created_at.strftime('%d/%m/%Y %H:%M'),
    } for r in reunions]
    return Response(data)

# ── MES RÉUNIONS (admin) ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_reunions(request):
    reunions = ReunionZoom.objects.filter(hote=request.user).order_by('-created_at')
    data = [{
        'id': r.id,
        'titre': r.titre,
        'meeting_id': r.meeting_id,
        'password': r.password,
        'join_url': r.join_url,
        'start_url': r.start_url,
        'statut': r.statut,
        'created_at': r.created_at.strftime('%d/%m/%Y %H:%M'),
    } for r in reunions]
    return Response(data)

# ── TERMINER RÉUNION ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminer_reunion(request, reunion_id):
    try:
        reunion = ReunionZoom.objects.get(id=reunion_id, hote=request.user)
    except ReunionZoom.DoesNotExist:
        return Response({'error': 'Réunion non trouvée'}, status=404)
    reunion.statut = 'terminee'
    reunion.save()
    return Response({'status': 'terminee'})
