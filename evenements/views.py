from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import Evenement, Actualite
import cloudinary.uploader

def evt_data(e):
    photo = ''
    if e.photo:
        try: photo = e.photo.url
        except: photo = ''
    if not photo and hasattr(e, 'photo_url') and e.photo_url:
        photo = e.photo_url
    return {
        'id': e.id, 'titre': e.titre, 'badge': e.badge,
        'badge_color': e.badge_color, 'date': e.date, 'lieu': e.lieu,
        'description': e.description, 'bouton': e.bouton, 'lien': e.lien,
        'photo': photo, 'statut': e.statut, 'ordre': e.ordre, 'actif': e.actif,
    }

def actu_data(a):
    photo = ''
    if a.photo:
        try: photo = a.photo.url
        except: photo = ''
    if not photo and hasattr(a, 'photo_url') and a.photo_url:
        photo = a.photo_url
    return {
        'id': a.id, 'titre': a.titre, 'categorie': a.categorie,
        'date': a.date, 'resume': a.resume, 'bouton': a.bouton,
        'lien': a.lien, 'photo': photo,
        'color': a.color, 'ordre': a.ordre, 'actif': a.actif,
    }

# ── ÉVÉNEMENTS ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def liste_evenements(request):
    evts = Evenement.objects.filter(actif=True)
    return Response([evt_data(e) for e in evts])

@api_view(['GET','POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_evenements(request):
    if request.method == 'GET':
        evts = Evenement.objects.all()
        return Response([evt_data(e) for e in evts])
    e = Evenement.objects.create(
        titre=request.data.get('titre',''),
        badge=request.data.get('badge',''),
        badge_color=request.data.get('badge_color','#C9A96A'),
        date=request.data.get('date',''),
        lieu=request.data.get('lieu',''),
        description=request.data.get('description',''),
        bouton=request.data.get('bouton',''),
        lien=request.data.get('lien',''),
        statut=request.data.get('statut','a_venir'),
        ordre=int(request.data.get('ordre',0)),
    )
    if 'photo' in request.FILES:
        e.photo = request.FILES['photo']
        e.save()
    elif 'photo_url' in request.data and request.data['photo_url']:
        e.photo_url = request.data['photo_url']
        e.save()
    return Response(evt_data(e), status=201)

@api_view(['PATCH','DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_evenement_detail(request, pk):
    try: e = Evenement.objects.get(pk=pk)
    except Evenement.DoesNotExist: return Response({'detail':'Introuvable'}, status=404)
    if request.method == 'DELETE':
        e.delete(); return Response(status=204)
    for field in ['titre','badge','badge_color','date','lieu','description','bouton','lien','statut','ordre','actif']:
        if field in request.data:
            val = request.data[field]
            if field == 'actif': val = val in [True,'true','1']
            if field == 'ordre':
                try: val = int(val)
                except: val = 0
            setattr(e, field, val)
    if 'photo' in request.FILES:
        e.photo = request.FILES['photo']
        if hasattr(e, 'photo_url'): e.photo_url = ''
    elif 'photo_url' in request.data and request.data['photo_url']:
        if hasattr(e, 'photo_url'): e.photo_url = request.data['photo_url']
    e.save()
    return Response(evt_data(e))

# ── ACTUALITÉS ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def liste_actualites(request):
    actus = Actualite.objects.filter(actif=True).order_by('ordre', '-created_at')
    return Response([actu_data(a) for a in actus])

@api_view(['GET','POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_actualites(request):
    if request.method == 'GET':
        actus = Actualite.objects.all().order_by('ordre', '-created_at')
        return Response([actu_data(a) for a in actus])
    a = Actualite.objects.create(
        titre=request.data.get('titre',''),
        categorie=request.data.get('categorie',''),
        date=request.data.get('date',''),
        resume=request.data.get('resume',''),
        bouton=request.data.get('bouton',''),
        lien=request.data.get('lien',''),
        color=request.data.get('color','#C9A96A'),
        ordre=int(request.data.get('ordre',0)),
    )
    if 'photo' in request.FILES:
        a.photo = request.FILES['photo']
        a.save()
    elif 'photo_url' in request.data and request.data['photo_url']:
        if hasattr(a, 'photo_url'): a.photo_url = request.data['photo_url']
        a.save()
    return Response(actu_data(a), status=201)

@api_view(['PATCH','DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_actualite_detail(request, pk):
    try: a = Actualite.objects.get(pk=pk)
    except Actualite.DoesNotExist: return Response({'detail':'Introuvable'}, status=404)
    if request.method == 'DELETE':
        a.delete(); return Response(status=204)
    for field in ['titre','categorie','date','resume','bouton','lien','color','ordre','actif']:
        if field in request.data:
            val = request.data[field]
            if field == 'actif': val = val in [True,'true','1']
            if field == 'ordre':
                try: val = int(val)
                except: val = 0
            setattr(a, field, val)
    if 'photo' in request.FILES:
        a.photo = request.FILES['photo']
        if hasattr(a, 'photo_url'): a.photo_url = ''
    elif 'photo_url' in request.data and request.data['photo_url']:
        if hasattr(a, 'photo_url'): a.photo_url = request.data['photo_url']
    a.save()
    return Response(actu_data(a))
