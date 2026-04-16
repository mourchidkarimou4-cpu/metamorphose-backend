from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Categorie, Cours, AccesCours
from paiement.models import Transaction
import hashlib, hmac, json

User = get_user_model()

def cours_data(c, user=None):
    a_acces = False
    if user and user.is_authenticated:
        a_acces = AccesCours.objects.filter(user=user, cours=c, actif=True).exists()
    return {
        'id':          c.id,
        'titre':       c.titre,
        'slug':        c.slug,
        'description': c.description,
        'categorie':   c.categorie.nom if c.categorie else '',
        'format':      c.format,
        'duree':       c.duree,
        'niveau':      c.niveau,
        'image':       c.image,
        'prix':        c.prix,
        'lien_achat':  c.lien_achat,
        'en_vedette':  c.en_vedette,
        'a_acces':     a_acces,
        # Contenu protégé — uniquement si accès
        'video_url':   c.video_url   if a_acces else '',
        'audio_url':   c.audio_url   if a_acces else '',
        'pdf_url':     c.pdf_url     if a_acces else '',
        'contenu':     c.contenu     if a_acces else '',
    }

# ── LISTE COURS PUBLIQUE ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def liste_cours(request):
    cours = Cours.objects.filter(actif=True)
    cat   = request.query_params.get('categorie')
    if cat:
        cours = cours.filter(categorie__slug=cat)
    user = request.user if request.user.is_authenticated else None
    return Response([cours_data(c, user) for c in cours])

# ── DETAIL COURS ─────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def detail_cours(request, slug):
    try:
        c = Cours.objects.get(slug=slug, actif=True)
    except Cours.DoesNotExist:
        return Response({'detail': 'Cours introuvable.'}, status=404)
    user = request.user if request.user.is_authenticated else None
    return Response(cours_data(c, user))

# ── MES COURS (utilisatrice connectée) ───────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_cours(request):
    acces = AccesCours.objects.filter(user=request.user, actif=True).select_related('cours')
    return Response([cours_data(a.cours, request.user) for a in acces])

# ── VÉRIFIER ACCÈS ───────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verifier_acces(request, slug):
    try:
        c = Cours.objects.get(slug=slug, actif=True)
    except Cours.DoesNotExist:
        return Response({'detail': 'Cours introuvable.'}, status=404)
    a_acces = AccesCours.objects.filter(user=request.user, cours=c, actif=True).exists()
    return Response({'a_acces': a_acces, 'cours': cours_data(c, request.user)})

# ── ADMIN — ACTIVER ACCÈS MANUELLEMENT ───────────────────────────
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_activer_acces(request):
    """
    Activation manuelle par Coach Prélia APEDO AHONON.
    Body : { "email": "...", "cours_id": 1, "notes": "..." }
    """
    email    = request.data.get('email', '').strip()
    cours_id = request.data.get('cours_id')
    notes    = request.data.get('notes', 'Activation manuelle — Coach Prélia APEDO AHONON')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Utilisatrice introuvable.'}, status=404)

    try:
        cours = Cours.objects.get(id=cours_id)
    except Cours.DoesNotExist:
        return Response({'detail': 'Cours introuvable.'}, status=404)

    acces, created = AccesCours.objects.update_or_create(
        user=user, cours=cours,
        defaults={'actif': True, 'source': 'manuel', 'notes': notes}
    )
    return Response({
        'detail': f"Acces {'cree' if created else 'reactive'} pour {user.email} — {cours.titre}.",
        'acces_id': acces.id,
    }, status=201 if created else 200)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_desactiver_acces(request):
    """
    Désactivation manuelle par Coach Prélia APEDO AHONON.
    Body : { "email": "...", "cours_id": 1 }
    """
    email    = request.data.get('email', '').strip()
    cours_id = request.data.get('cours_id')

    try:
        user  = User.objects.get(email=email)
        cours = Cours.objects.get(id=cours_id)
        acces = AccesCours.objects.get(user=user, cours=cours)
        acces.actif = False
        acces.save()
        return Response({'detail': f"Acces desactive pour {user.email}."})
    except (User.DoesNotExist, Cours.DoesNotExist, AccesCours.DoesNotExist):
        return Response({'detail': 'Acces introuvable.'}, status=404)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_liste_acces(request):
    """Liste tous les accès — tableau de bord Coach Prélia APEDO AHONON."""
    acces = AccesCours.objects.select_related('user', 'cours').all()
    cours_id = request.query_params.get('cours_id')
    if cours_id:
        acces = acces.filter(cours_id=cours_id)
    return Response([{
        'id':         a.id,
        'email':      a.user.email,
        'prenom':     a.user.first_name,
        'cours':      a.cours.titre,
        'cours_id':   a.cours.id,
        'source':     a.get_source_display(),
        'actif':      a.actif,
        'notes':      a.notes,
        'created_at': a.created_at.strftime('%d/%m/%Y %H:%M'),
    } for a in acces])

# ── WEBHOOK PAIEMENT ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def webhook_paiement(request):
    """
    Webhook générique — reçoit la confirmation de paiement externe.
    Active automatiquement l'accès au cours concerné.
    Body attendu : { "email": "...", "cours_id": 1, "transaction_id": "...", "montant": 5000, "signature": "..." }
    """
    import os
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')
    if not WEBHOOK_SECRET:
        return Response({'detail': 'Webhook non configuré.'}, status=500)

    # Vérification signature HMAC
    signature_recue    = request.headers.get('X-Webhook-Signature', '')
    if not signature_recue:
        return Response({'detail': 'Signature manquante.'}, status=400)

    payload_bytes      = request.body
    signature_calculee = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature_recue, signature_calculee):
        return Response({'detail': 'Signature invalide.'}, status=403)

    email          = request.data.get('email', '').strip()
    cours_id       = request.data.get('cours_id')
    transaction_id = request.data.get('transaction_id', '')
    montant        = request.data.get('montant', 0)

    try:
        user  = User.objects.get(email=email)
        cours = Cours.objects.get(id=cours_id, actif=True)
    except (User.DoesNotExist, Cours.DoesNotExist):
        return Response({'detail': 'Email ou cours introuvable.'}, status=404)

    # Créer la transaction
    transaction, _ = Transaction.objects.get_or_create(
        transaction_id=transaction_id,
        defaults={
            'user':         user,
            'montant':      montant,
            'statut':       'success',
            'source':       'webhook',
            'email_client': email,
        }
    )

    # Activer l'accès
    AccesCours.objects.update_or_create(
        user=user, cours=cours,
        defaults={
            'actif':       True,
            'source':      'webhook',
            'transaction': transaction,
            'notes':       f"Activation automatique via webhook — transaction {transaction_id}",
        }
    )

    return Response({'detail': f"Acces active pour {user.email} — {cours.titre}."})

# ── CATEGORIES ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def liste_categories(request):
    cats = Categorie.objects.all()
    return Response([{'id': c.id, 'nom': c.nom, 'slug': c.slug, 'couleur': c.couleur} for c in cats])

# ── ADMIN CRUD COURS & CATÉGORIES ────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_cours(request):
    if not request.user.is_staff:
        return Response({'detail': 'Accès refusé.'}, status=403)
    if request.method == 'GET':
        cours = Cours.objects.select_related('categorie').all()
        return Response([cours_data(c, request.user) for c in cours])
    # POST
    data = request.data
    try:
        c = Cours.objects.create(
            titre=data['titre'], slug=data['slug'],
            description=data.get('description',''),
            format=data.get('format','texte'),
            contenu=data.get('contenu',''),
            video_url=data.get('video_url',''),
            audio_url=data.get('audio_url',''),
            pdf_url=data.get('pdf_url',''),
            duree=data.get('duree',''),
            niveau=data.get('niveau','debutant'),
            image=data.get('image',''),
            semaine=data.get('semaine') or None,
            actif=data.get('actif', True),
            en_vedette=data.get('en_vedette', False),
            ordre=data.get('ordre', 0),
            prix=data.get('prix', 0),
            lien_achat=data.get('lien_achat',''),
            categorie_id=data.get('categorie') or None,
        )
        return Response(cours_data(c, request.user), status=201)
    except Exception as e:
        return Response({'detail': str(e)}, status=400)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_cours_detail(request, pk):
    if not request.user.is_staff:
        return Response({'detail': 'Accès refusé.'}, status=403)
    try:
        c = Cours.objects.get(pk=pk)
    except Cours.DoesNotExist:
        return Response({'detail': 'Cours introuvable.'}, status=404)
    if request.method == 'GET':
        return Response(cours_data(c, request.user))
    if request.method == 'DELETE':
        c.delete()
        return Response(status=204)
    # PATCH
    data = request.data
    for field in ['titre','slug','description','format','contenu','video_url','audio_url','pdf_url','duree','niveau','image','actif','en_vedette','ordre','prix','lien_achat']:
        if field in data:
            setattr(c, field, data[field])
    if 'semaine' in data:
        c.semaine = data['semaine'] or None
    if 'categorie' in data:
        c.categorie_id = data['categorie'] or None
    c.save()
    return Response(cours_data(c, request.user))

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_categories(request):
    if not request.user.is_staff:
        return Response({'detail': 'Accès refusé.'}, status=403)
    if request.method == 'GET':
        from django.forms.models import model_to_dict
        cats = Categorie.objects.all()
        return Response([{'id':c.id,'nom':c.nom,'slug':c.slug,'icone':c.icone,'couleur':c.couleur,'ordre':c.ordre} for c in cats])
    data = request.data
    try:
        cat = Categorie.objects.create(
            nom=data['nom'], slug=data['slug'],
            icone=data.get('icone','✦'),
            couleur=data.get('couleur','#C9A96A'),
            ordre=data.get('ordre',0),
        )
        return Response({'id':cat.id,'nom':cat.nom,'slug':cat.slug,'icone':cat.icone,'couleur':cat.couleur,'ordre':cat.ordre}, status=201)
    except Exception as e:
        return Response({'detail': str(e)}, status=400)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_categorie_detail(request, pk):
    if not request.user.is_staff:
        return Response({'detail': 'Accès refusé.'}, status=403)
    try:
        cat = Categorie.objects.get(pk=pk)
    except Categorie.DoesNotExist:
        return Response({'detail': 'Catégorie introuvable.'}, status=404)
    if request.method == 'DELETE':
        cat.delete()
        return Response(status=204)
    data = request.data
    for field in ['nom','slug','icone','couleur','ordre']:
        if field in data:
            setattr(cat, field, data[field])
    cat.save()
    return Response({'id':cat.id,'nom':cat.nom,'slug':cat.slug,'icone':cat.icone,'couleur':cat.couleur,'ordre':cat.ordre})
