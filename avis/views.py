from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import Temoignage
from .serializers import TemoignagePublicSerializer, TemoignageCreateSerializer, TemoignageAdminSerializer

# ── PUBLIC ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def liste_publique(request):
    qs = Temoignage.objects.filter(statut='approuve')
    vedette = request.query_params.get('vedette')
    formule = request.query_params.get('formule')
    if vedette: qs = qs.filter(en_vedette=True)
    if formule: qs = qs.filter(formule=formule)
    return Response(TemoignagePublicSerializer(qs, many=True, context={'request':request}).data)

# ── MEMBRE ──────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def soumettre(request):
    s = TemoignageCreateSerializer(data=request.data)
    if s.is_valid():
        t = s.save(
            user=request.user,
            pays=request.user.pays or request.data.get('pays',''),
            formule=request.user.formule or request.data.get('formule',''),
            statut='en_attente',
        )
        if 'photo_avant' in request.FILES:
            t.photo_avant = request.FILES['photo_avant']
        if 'photo_apres' in request.FILES:
            t.photo_apres = request.FILES['photo_apres']
        t.save()
        return Response({'detail': 'Témoignage soumis.', 'id': t.id}, status=201)
    return Response(s.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_temoignages(request):
    qs = Temoignage.objects.filter(user=request.user)
    return Response(TemoignagePublicSerializer(qs, many=True, context={'request':request}).data)

# ── ADMIN ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_admin(request):
    statut = request.query_params.get('statut', '')
    limit  = min(int(request.query_params.get('limit',  100)), 500)
    offset = int(request.query_params.get('offset', 0))
    qs = Temoignage.objects.all()
    if statut:
        qs = qs.filter(statut=statut)
    total = qs.count()
    page  = qs[offset:offset + limit]
    return Response({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': TemoignageAdminSerializer(page, many=True, context={'request': request}).data,
    })

def _save_fichiers(t, files):
    """Sauvegarde les fichiers uploadés sur le témoignage"""
    changed = False
    if 'photo_avant' in files:
        t.photo_avant = files['photo_avant']; changed = True
    if 'photo_apres' in files:
        t.photo_apres = files['photo_apres']; changed = True
    if 'video_fichier' in files:
        t.video_fichier = files['video_fichier']; changed = True
    if 'audio_fichier' in files:
        t.audio_fichier = files['audio_fichier']; changed = True
    if changed:
        t.save()
    return t

@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def ajouter(request):
    s = TemoignageAdminSerializer(data=request.data)
    if s.is_valid():
        t = s.save()
        t = _save_fichiers(t, request.FILES)
        return Response(TemoignageAdminSerializer(t, context={'request':request}).data, status=201)
    return Response(s.errors, status=400)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def modifier_complet(request, pk):
    try:
        t = Temoignage.objects.get(pk=pk)
    except Temoignage.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)
    s = TemoignageAdminSerializer(t, data=request.data, partial=True)
    if s.is_valid():
        t = s.save()
        t = _save_fichiers(t, request.FILES)
        return Response(TemoignageAdminSerializer(t, context={'request':request}).data)
    return Response(s.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def approuver(request, pk):
    try:
        t = Temoignage.objects.get(pk=pk)
        t.statut = 'approuve'; t.save()
        return Response({'detail':'Approuvé.'})
    except Temoignage.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def refuser(request, pk):
    try:
        t = Temoignage.objects.get(pk=pk)
        t.statut = 'refuse'; t.save()
        return Response({'detail':'Refusé.'})
    except Temoignage.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def supprimer(request, pk):
    try:
        Temoignage.objects.get(pk=pk).delete()
        return Response(status=204)
    except Temoignage.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)
