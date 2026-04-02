from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import HttpResponse
from contenu.models import Guide, Replay, DemandeContact
from .models import SiteConfig
from .serializers import (
    AdminUserSerializer, AdminGuideSerializer,
    AdminReplaySerializer, AdminDemandeSerializer,
    SiteConfigSerializer,
)
import csv

User = get_user_model()

# ── STATS ──────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdminUser])
def stats(request):
    return Response({
        'membres':     User.objects.filter(is_staff=False).count(),
        'actifs':      User.objects.filter(actif=True).count(),
        'demandes':    DemandeContact.objects.count(),
        'non_traites': DemandeContact.objects.filter(traite=False).count(),
        'replays':     Replay.objects.count(),
        'guides':      Guide.objects.count(),
        'formules': {
            'F1': User.objects.filter(formule='F1').count(),
            'F2': User.objects.filter(formule='F2').count(),
            'F3': User.objects.filter(formule='F3').count(),
            'F4': User.objects.filter(formule='F4').count(),
        }
    })

# ── MEMBRES ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdminUser])
def membres_list(request):
    qs = User.objects.filter(is_staff=False).order_by('-date_joined')
    return Response(AdminUserSerializer(qs, many=True).data)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def membre_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        user.delete()
        return Response(status=204)
    s = AdminUserSerializer(user, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)

# ── DEMANDES ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdminUser])
def demandes_list(request):
    qs = DemandeContact.objects.order_by('-date')
    return Response(AdminDemandeSerializer(qs, many=True).data)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def demande_detail(request, pk):
    try:
        d = DemandeContact.objects.get(pk=pk)
    except DemandeContact.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        d.delete()
        return Response(status=204)
    s = AdminDemandeSerializer(d, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)

# ── REPLAYS ────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def replays_list(request):
    if request.method == 'GET':
        return Response(AdminReplaySerializer(Replay.objects.order_by('semaine'), many=True).data)
    s = AdminReplaySerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def replay_detail(request, pk):
    try:
        r = Replay.objects.get(pk=pk)
    except Replay.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        r.delete()
        return Response(status=204)
    s = AdminReplaySerializer(r, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)

# ── GUIDES ─────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def guides_list(request):
    if request.method == 'GET':
        return Response(AdminGuideSerializer(
            Guide.objects.order_by('numero'), many=True,
            context={'request': request}
        ).data)
    s = AdminGuideSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def guide_detail(request, pk):
    try:
        g = Guide.objects.get(pk=pk)
    except Guide.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        g.delete()
        return Response(status=204)
    s = AdminGuideSerializer(g, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)

# ── SITE CONFIG ────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdminUser])
def config_list(request):
    return Response(SiteConfigSerializer(SiteConfig.objects.all().order_by('section'), many=True).data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def config_update(request):
    cle     = request.data.get('cle')
    valeur  = request.data.get('valeur')
    section = request.data.get('section', 'general')
    if not cle:
        return Response({'detail': 'Clé requise.'}, status=400)
    obj, _ = SiteConfig.objects.update_or_create(
        cle=cle, defaults={'valeur': valeur, 'section': section}
    )
    return Response(SiteConfigSerializer(obj).data)

@api_view(['GET'])
@permission_classes([AllowAny])
def config_public(request):
    """Textes publics du site — accessible sans authentification"""
    return Response(SiteConfigSerializer(SiteConfig.objects.all().order_by('section'), many=True).data)

# ── IMAGE UPLOAD — Cloudinary ──────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def image_upload(request):
    fichier = request.FILES.get('fichier')
    cle     = request.data.get('cle')
    section = request.data.get('section', 'images')

    if not fichier or not cle:
        return Response({'detail': 'Fichier et cle requis.'}, status=400)

    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(
            fichier,
            folder='metamorphose',
            public_id=cle,
            overwrite=True,
            resource_type='auto',
        )
        url = result.get('secure_url', '')
    except Exception as e:
        return Response({'detail': f'Erreur Cloudinary : {str(e)}'}, status=500)

    obj, _ = SiteConfig.objects.update_or_create(
        cle=cle, defaults={'valeur': url, 'section': section}
    )
    return Response({'url': url, 'cle': cle})

# ── LISTE ATTENTE ──────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAdminUser])
def liste_attente_admin(request):
    from administration.models import ListeAttente
    data = list(ListeAttente.objects.values("id","email","prenom","date","notifie"))
    return Response(data)

@api_view(["POST"])
@permission_classes([AllowAny])
def inscrire_liste_attente(request):
    from administration.models import ListeAttente
    email  = request.data.get("email","").strip()
    prenom = request.data.get("prenom","").strip()
    if not email:
        return Response({"detail":"Email requis."}, status=400)
    obj, created = ListeAttente.objects.get_or_create(email=email, defaults={"prenom":prenom})
    return Response({"detail":"Inscription confirmée."}, status=201 if created else 200)

@api_view(["POST"])
@permission_classes([IsAdminUser])
def notifier_liste_attente(request):
    from administration.models import ListeAttente
    from django.core.mail import send_mail
    personnes = ListeAttente.objects.filter(notifie=False)
    count = 0
    for p in personnes:
        try:
            send_mail(
                subject="Les inscriptions sont ouvertes — Méta'Morph'Ose",
                message=f"Bonjour {p.prenom or 'belle femme'},\n\nLes inscriptions sont maintenant ouvertes !\n\nPrélia Apedo",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[p.email],
                fail_silently=True,
            )
            p.notifie = True; p.save()
            count += 1
        except: pass
    return Response({"detail": f"{count} personnes notifiées."})

@api_view(["POST"])
@permission_classes([IsAdminUser])
def envoyer_newsletter(request):
    from accounts.models import CustomUser
    from django.core.mail import send_mail
    sujet   = request.data.get("sujet","")
    message = request.data.get("message","")
    cible   = request.data.get("cible","tous")
    if not sujet or not message:
        return Response({"detail":"Sujet et message requis."}, status=400)
    users = CustomUser.objects.filter(is_staff=False, actif=True)
    if cible != "tous":
        users = users.filter(formule=cible)
    count = 0
    for user in users:
        try:
            send_mail(
                subject=sujet,
                message=f"Bonjour {user.first_name or user.email},\n\n{message}\n\nPrélia Apedo",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            count += 1
        except: pass
    return Response({"detail": f"Email envoyé à {count} membre{'s' if count>1 else ''}."})

@api_view(["POST"])
@permission_classes([IsAdminUser])
def toggle_maintenance(request):
    actif = request.data.get("actif", False)
    SiteConfig.objects.update_or_create(
        cle="maintenance_active",
        defaults={"valeur":"1" if actif else "0","section":"systeme"}
    )
    return Response({"maintenance": actif})

@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_temoignages_csv(request):
    from avis.models import Temoignage
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="temoignages_metamorphose.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(["Prénom","Pays","Formule","Type","Note","Texte","Statut","En vedette","Date"])
    for t in Temoignage.objects.all().order_by("-date"):
        writer.writerow([t.prenom, t.pays or "", t.formule or "", t.type_temo, t.note, t.texte or "", t.statut, "Oui" if t.en_vedette else "Non", t.date.strftime("%d/%m/%Y %H:%M")])
    return response

@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_attente_csv(request):
    from administration.models import ListeAttente
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="liste_attente.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(["Prénom","Email","Date","Notifiée"])
    for p in ListeAttente.objects.all():
        writer.writerow([p.prenom or "", p.email, p.date.strftime("%d/%m/%Y %H:%M"), "Oui" if p.notifie else "Non"])
    return response

@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_membres_csv(request):
    from accounts.models import CustomUser
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="membres_metamorphose.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(["Prénom","Nom","Email","WhatsApp","Pays","Formule","Actif","Date inscription"])
    for u in CustomUser.objects.filter(is_staff=False).order_by("-date_joined"):
        writer.writerow([u.first_name, u.last_name, u.email, u.whatsapp or "", u.pays or "", u.formule or "", "Oui" if u.actif else "Non", u.date_joined.strftime("%d/%m/%Y %H:%M")])
    return response

@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_demandes_csv(request):
    from contenu.models import DemandeContact
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="demandes_metamorphose.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(["Prénom","Nom","Email","WhatsApp","Pays","Formule","Message","Date"])
    for d in DemandeContact.objects.all().order_by("-date"):
        writer.writerow([d.prenom or "", d.nom or "", d.email or "", d.whatsapp or "", d.pays or "", d.formule or "", d.message or "", d.date.strftime("%d/%m/%Y %H:%M")])
    return response
