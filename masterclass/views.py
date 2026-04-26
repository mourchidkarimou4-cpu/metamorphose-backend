from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.utils import timezone
from .models import Masterclass, Reservation

def mc_data(m):
    return {
        'id':               m.id,
        'titre':            m.titre,
        'description':      m.description,
        'date':             m.date.strftime('%d/%m/%Y à %Hh%M'),
        'image':            m.image.url if m.image else '',
        'places_max':       m.places_max,
        'places_restantes': m.places_restantes,
        'complet':          m.complet,
        'gratuite':         m.gratuite,
        'lien_live':        m.lien_live,
    }

@api_view(['GET'])
@permission_classes([AllowAny])
def liste_masterclasses(request):
    mcs = Masterclass.objects.filter(est_active=True, date__gte=timezone.now())
    return Response([mc_data(m) for m in mcs])

@api_view(['POST'])
@permission_classes([AllowAny])
def reserver(request, pk):
    try:
        mc = Masterclass.objects.get(pk=pk, est_active=True)
    except Masterclass.DoesNotExist:
        return Response({'detail': 'Masterclass introuvable.'}, status=404)

    if mc.complet:
        return Response({'detail': 'Cette masterclass est complète.'}, status=400)

    email = request.data.get('email', '').strip()
    if not email:
        return Response({'detail': 'Email requis.'}, status=400)

    if Reservation.objects.filter(masterclass=mc, email=email).exists():
        return Response({'detail': 'Vous êtes déjà inscrit à cette masterclass.'}, status=400)

    r = Reservation.objects.create(
        masterclass=mc,
        prenom=request.data.get('prenom', ''),
        nom=request.data.get('nom', ''),
        email=email,
        telephone=request.data.get('telephone', ''),
        user=request.user if request.user.is_authenticated else None,
    )
    return Response({
        'detail': 'Inscription confirmée.',
        'prenom': r.prenom,
        'masterclass': mc.titre,
        'date': mc.date.strftime('%d/%m/%Y à %Hh%M'),
    }, status=201)

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_masterclasses(request):
    if request.method == 'GET':
        mcs = Masterclass.objects.all()
        return Response([{**mc_data(m), 'est_active': m.est_active} for m in mcs])

    mc = Masterclass.objects.create(
        titre=request.data.get('titre', ''),
        description=request.data.get('description', ''),
        date=request.data.get('date'),
        places_max=int(request.data.get('places_max', 100)),
        est_active=request.data.get('est_active', True) in [True, 'true', '1'],
        gratuite=request.data.get('gratuite', True) in [True, 'true', '1'],
        lien_live=request.data.get('lien_live', ''),
    )
    if 'image' in request.FILES:
        mc.image = request.FILES['image']
        mc.save()
    return Response(mc_data(mc), status=201)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_masterclass_detail(request, pk):
    try:
        mc = Masterclass.objects.get(pk=pk)
    except Masterclass.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)

    if request.method == 'DELETE':
        mc.delete()
        return Response(status=204)

    for field in ['titre', 'description', 'date', 'places_max', 'lien_live']:
        if field in request.data:
            setattr(mc, field, request.data[field])
    for field in ['est_active', 'gratuite']:
        if field in request.data:
            setattr(mc, field, request.data[field] in [True, 'true', '1'])
    if 'image' in request.FILES:
        mc.image = request.FILES['image']
    mc.save()
    return Response(mc_data(mc))

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_reservations(request, pk):
    try:
        mc = Masterclass.objects.get(pk=pk)
    except Masterclass.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    return Response([{
        'id':        r.id,
        'prenom':    r.prenom,
        'nom':       r.nom,
        'email':     r.email,
        'telephone': r.telephone,
        'created_at':r.created_at.strftime('%d/%m/%Y %H:%M'),
    } for r in mc.reservations.all()])


# ── Témoignages Masterclass ──────────────────────────────────────────────────
from .models import TemoignageMasterclass
import cloudinary.uploader

@csrf_exempt
def temoignages_masterclass_liste(request):
    """GET /api/masterclass/temoignages/ — liste publique"""
    from django.http import JsonResponse
    temos = TemoignageMasterclass.objects.filter(actif=True)
    data = []
    for t in temos:
        data.append({
            "id":     t.id,
            "prenom": t.prenom,
            "texte":  t.texte,
            "photo":  t.photo.url if t.photo else "",
            "ordre":  t.ordre,
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def temoignages_masterclass_admin(request):
    """POST /api/masterclass/temoignages/ajouter/ — ajouter"""
    from django.http import JsonResponse
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)
    prenom = request.POST.get("prenom", "").strip()
    texte  = request.POST.get("texte", "").strip()
    ordre  = request.POST.get("ordre", 0)
    photo  = request.FILES.get("photo")
    if not prenom:
        return JsonResponse({"error": "Prénom requis"}, status=400)
    from django.http import JsonResponse as JR
    try:
        t = TemoignageMasterclass(prenom=prenom, texte=texte, ordre=ordre)
        if photo:
            result = cloudinary.uploader.upload(photo, folder="metamorphose/masterclass/temoignages")
            t.photo = result["public_id"]
        t.save()
        photo_url = t.photo.url if hasattr(t.photo, "url") else (f"https://res.cloudinary.com/dp7v6vlgs/image/upload/{t.photo}" if t.photo else "")
        return JsonResponse({"id": t.id, "prenom": t.prenom, "photo": photo_url})
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "trace": traceback.format_exc()}, status=500)

@csrf_exempt
def temoignage_masterclass_supprimer(request, pk):
    """DELETE /api/masterclass/temoignages/<pk>/supprimer/"""
    from django.http import JsonResponse
    try:
        t = TemoignageMasterclass.objects.get(pk=pk)
        t.delete()
        return JsonResponse({"status": "ok"})
    except TemoignageMasterclass.DoesNotExist:
        return JsonResponse({"error": "Non trouvé"}, status=404)
