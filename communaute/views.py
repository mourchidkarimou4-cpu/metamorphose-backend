from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import CleAcces, Publication, Commentaire, ProfilCommunaute

User = get_user_model()

def pub_data(p, request_user=None):
    return {
        'id': str(p.id),
        'auteure': p.auteure.first_name or p.auteure.email,
        'auteure_id': p.auteure.id,
        'contenu': p.contenu,
        'type_media': p.type_media,
        'media': p.media.url if p.media else '',
        'pour_coach': p.pour_coach,
        'epingle': p.epingle,
        'nb_commentaires': p.commentaires.filter(visible=True).count(),
        'created_at': p.created_at.strftime('%d/%m/%Y %H:%M'),
        'est_moi': request_user and p.auteure.id == request_user.id,
    }

def com_data(c, request_user=None):
    return {
        'id': str(c.id),
        'auteure': c.auteure.first_name or c.auteure.email,
        'auteure_id': c.auteure.id,
        'contenu': c.contenu,
        'est_coach': c.est_coach,
        'created_at': c.created_at.strftime('%d/%m/%Y %H:%M'),
        'est_moi': request_user and c.auteure.id == request_user.id,
    }

# ── ACCÈS ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def valider_cle(request):
    cle = request.data.get('cle', '').strip()
    if not cle:
        return Response({'detail': 'Clé requise.'}, status=400)
    try:
        acces = CleAcces.objects.get(cle=cle, active=True)
    except CleAcces.DoesNotExist:
        return Response({'detail': 'Clé invalide ou expirée.'}, status=403)

    if acces.utilisatrice.id != request.user.id:
        return Response({'detail': 'Cette clé ne vous appartient pas.'}, status=403)

    premiere = acces.premiere_connexion
    if premiere:
        acces.premiere_connexion = False
        acces.utilisee_le = timezone.now()
        acces.save()
        # Créer profil communauté si absent
        ProfilCommunaute.objects.get_or_create(utilisatrice=request.user)

    return Response({'acces': True, 'premiere_connexion': premiere})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verifier_acces(request):
    try:
        acces = CleAcces.objects.get(utilisatrice=request.user, active=True)
        premiere = acces.premiere_connexion
        return Response({'acces': True, 'premiere_connexion': premiere})
    except CleAcces.DoesNotExist:
        return Response({'acces': False})

# ── ADMIN — Générer une clé ───────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAdminUser])
def generer_cle(request):
    email = request.data.get('email', '').strip()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Utilisatrice introuvable.'}, status=404)
    acces = CleAcces.generer(user)
    return Response({'cle': acces.cle, 'email': user.email})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_cles(request):
    cles = CleAcces.objects.select_related('utilisatrice').all().order_by('-creee_le')
    return Response([{
        'id': c.id,
        'email': c.utilisatrice.email,
        'prenom': c.utilisatrice.first_name,
        'cle': c.cle,
        'active': c.active,
        'premiere_connexion': c.premiere_connexion,
        'creee_le': c.creee_le.strftime('%d/%m/%Y'),
        'utilisee_le': c.utilisee_le.strftime('%d/%m/%Y %H:%M') if c.utilisee_le else '',
    } for c in cles])

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_cle(request, pk):
    try:
        acces = CleAcces.objects.get(pk=pk)
    except CleAcces.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    acces.active = not acces.active
    acces.save()
    return Response({'active': acces.active})

# ── PUBLICATIONS ──────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def publications(request):
    # Vérifier accès communauté
    if not CleAcces.objects.filter(utilisatrice=request.user, active=True).exists():
        return Response({'detail': 'Accès refusé.'}, status=403)

    if request.method == 'GET':
        pour_coach = request.query_params.get('pour_coach')
        qs = Publication.objects.filter(visible=True).select_related('auteure')
        if pour_coach == '1':
            qs = qs.filter(pour_coach=True)
        return Response([pub_data(p, request.user) for p in qs])

    # POST — créer publication
    contenu = request.data.get('contenu', '').strip()
    if not contenu:
        return Response({'detail': 'Contenu requis.'}, status=400)

    p = Publication.objects.create(
        auteure=request.user,
        contenu=contenu,
        type_media=request.data.get('type_media', 'texte'),
        pour_coach=request.data.get('pour_coach', False) in [True, 'true', '1'],
    )
    if 'media' in request.FILES:
        p.media = request.FILES['media']
        p.save()

    return Response(pub_data(p, request.user), status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_publication(request, pk):
    try:
        p = Publication.objects.get(id=pk)
    except Publication.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if p.auteure.id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Non autorisé.'}, status=403)
    p.visible = False
    p.save()
    return Response(status=204)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def epingler_publication(request, pk):
    try:
        p = Publication.objects.get(id=pk)
    except Publication.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    p.epingle = not p.epingle
    p.save()
    return Response({'epingle': p.epingle})

# ── COMMENTAIRES ──────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def commentaires(request, pub_id):
    if not CleAcces.objects.filter(utilisatrice=request.user, active=True).exists():
        return Response({'detail': 'Accès refusé.'}, status=403)

    try:
        pub = Publication.objects.get(id=pub_id, visible=True)
    except Publication.DoesNotExist:
        return Response({'detail': 'Publication introuvable.'}, status=404)

    if request.method == 'GET':
        coms = pub.commentaires.filter(visible=True)
        return Response([com_data(c, request.user) for c in coms])

    contenu = request.data.get('contenu', '').strip()
    if not contenu:
        return Response({'detail': 'Contenu requis.'}, status=400)

    c = Commentaire.objects.create(
        publication=pub,
        auteure=request.user,
        contenu=contenu,
        est_coach=request.user.is_staff,
    )
    return Response(com_data(c, request.user), status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_commentaire(request, pk):
    try:
        c = Commentaire.objects.get(id=pk)
    except Commentaire.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if c.auteure.id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Non autorisé.'}, status=403)
    c.visible = False
    c.save()
    return Response(status=204)

# ── PROFIL ────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profil_communaute(request):
    profil, _ = ProfilCommunaute.objects.get_or_create(utilisatrice=request.user)
    if request.method == 'GET':
        return Response({
            'presentation': profil.presentation,
            'secteur': profil.secteur,
            'pays': profil.pays,
            'situation_mat': profil.situation_mat,
            'passion': profil.passion,
            'apport_metamorphose': profil.apport_metamorphose,
            'attentes': profil.attentes,
            'onboarding_fait': profil.onboarding_fait,
        })
    for field in ['presentation','secteur','pays','situation_mat','passion','apport_metamorphose','attentes']:
        if field in request.data:
            setattr(profil, field, request.data[field])
    if 'onboarding_fait' in request.data:
        profil.onboarding_fait = True
    profil.save()
    return Response({'detail': 'Profil mis à jour.'})
