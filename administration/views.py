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
    from datetime import date, timedelta
    from django.db.models import Count
    from django.db.models.functions import TruncMonth, TruncWeek

    aujourd_hui = date.today()
    il_y_a_30j  = aujourd_hui - timedelta(days=30)
    il_y_a_7j   = aujourd_hui - timedelta(days=7)

    # ── Membres ───────────────────────────────────────────────────
    membres_qs = User.objects.filter(is_staff=False)
    total_membres   = membres_qs.count()
    membres_actifs  = membres_qs.filter(actif=True).count()
    nouveaux_7j     = membres_qs.filter(date_joined__date__gte=il_y_a_7j).count()
    nouveaux_30j    = membres_qs.filter(date_joined__date__gte=il_y_a_30j).count()

    # ── Inscriptions par mois (12 derniers mois) ─────────────────
    inscriptions_mois = list(
        membres_qs
        .filter(date_joined__date__gte=aujourd_hui - timedelta(days=365))
        .annotate(mois=TruncMonth('date_joined'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
        .values('mois', 'total')
    )

    # ── Répartition formules & revenus estimés ───────────────────
    PRIX_FORMULES = {'F1': 65000, 'F2': 150000, 'F3': 250000, 'F4': 350000}
    formules = {}
    revenu_estime = 0
    for code, prix in PRIX_FORMULES.items():
        count = membres_qs.filter(formule=code, actif=True).count()
        formules[code] = count
        revenu_estime += count * prix

    # ── Taux de conversion demandes → membres ─────────────────────
    total_demandes  = DemandeContact.objects.count()
    taux_conversion = round((membres_actifs / total_demandes * 100), 1) if total_demandes > 0 else 0

    # ── Demandes récentes ─────────────────────────────────────────
    demandes_7j = DemandeContact.objects.filter(
        created_at__date__gte=il_y_a_7j
    ).count() if hasattr(DemandeContact, 'created_at') else 0

    return Response({
        # Métriques principales
        'membres':          total_membres,
        'actifs':           membres_actifs,
        'taux_activation':  round(membres_actifs / total_membres * 100, 1) if total_membres > 0 else 0,
        'nouveaux_7j':      nouveaux_7j,
        'nouveaux_30j':     nouveaux_30j,

        # Demandes
        'demandes':         total_demandes,
        'non_traites':      DemandeContact.objects.filter(traite=False).count(),
        'demandes_7j':      demandes_7j,
        'taux_conversion':  taux_conversion,

        # Contenu
        'replays':          Replay.objects.count(),
        'guides':           Guide.objects.count(),

        # Formules et revenus
        'formules':         formules,
        'revenu_estime':    revenu_estime,

        # Tendance inscriptions
        'inscriptions_mois': [
            {
                'mois':  item['mois'].strftime('%b %Y') if item['mois'] else '',
                'total': item['total']
            }
            for item in inscriptions_mois
        ],
    })

# ── MEMBRES ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdminUser])
def membres_list(request):
    limit  = min(int(request.query_params.get('limit',  200)), 500)
    offset = int(request.query_params.get('offset', 0))
    qs     = User.objects.filter(is_staff=False).order_by('-date_joined')
    total  = qs.count()
    page   = qs[offset:offset + limit]
    return Response({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': AdminUserSerializer(page, many=True).data,
    })

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
    """Textes publics du site — accessible sans authentification.
    CORRECTION : filtre les sections sensibles (systeme, prive, admin, interne)
    pour ne pas exposer accidentellement des données internes."""
    # Filtre insensible à la casse — couvre "Systeme", "système", "ADMIN"…
    qs = SiteConfig.objects.all().order_by('section')
    for section in ('systeme', 'prive', 'admin', 'interne'):
        qs = qs.exclude(section__iexact=section)
    return Response(SiteConfigSerializer(qs, many=True).data)

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
    for t in Temoignage.objects.all().order_by("-date")[:5000]:
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
    for p in ListeAttente.objects.all()[:5000]:
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
    for u in CustomUser.objects.filter(is_staff=False).order_by("-date_joined")[:5000]:
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
    for d in DemandeContact.objects.all().order_by("-date")[:5000]:
        writer.writerow([d.prenom or "", d.nom or "", d.email or "", d.whatsapp or "", d.pays or "", d.formule or "", d.message or "", d.date.strftime("%d/%m/%Y %H:%M")])
    return response


@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_abonnes_csv(request):
    from contenu.models import Abonne
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="abonnes_newsletter.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(["Email", "Prénom", "Actif", "Date inscription"])
    for a in Abonne.objects.all().order_by("-created_at")[:5000]:
        writer.writerow([
            a.email, a.prenom or "",
            "Oui" if a.actif else "Non",
            a.created_at.strftime("%d/%m/%Y %H:%M")
        ])
    return response

# ── PARTENAIRES ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def partenaires_public(request):
    from .models import Partenaire
    partenaires = Partenaire.objects.filter(actif=True)
    data = [{'id':p.id,'nom':p.nom,'logo':p.logo,'lien':p.lien,'ordre':p.ordre} for p in partenaires]
    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def partenaires_list(request):
    from .models import Partenaire
    if request.method == 'GET':
        partenaires = Partenaire.objects.all()
        data = [{'id':p.id,'nom':p.nom,'logo':p.logo,'lien':p.lien,'ordre':p.ordre,'actif':p.actif} for p in partenaires]
        return Response(data)
    nom = request.data.get('nom','')
    if not nom:
        return Response({'detail':'Nom requis.'}, status=400)
    p = Partenaire.objects.create(
        nom=nom, logo=request.data.get('logo',''),
        lien=request.data.get('lien',''), ordre=request.data.get('ordre',0)
    )
    return Response({'id':p.id,'nom':p.nom,'logo':p.logo,'lien':p.lien,'ordre':p.ordre,'actif':p.actif}, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def partenaire_detail(request, pk):
    from .models import Partenaire
    try:
        p = Partenaire.objects.get(pk=pk)
    except Partenaire.DoesNotExist:
        return Response({'detail':'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        p.delete()
        return Response(status=204)
    for field in ['nom','logo','lien','ordre','actif']:
        if field in request.data:
            setattr(p, field, request.data[field])
    p.save()
    return Response({'id':p.id,'nom':p.nom,'logo':p.logo,'lien':p.lien,'ordre':p.ordre,'actif':p.actif})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def partenaire_logo_upload(request):
    fichier = request.FILES.get('fichier')
    if not fichier:
        return Response({'detail':'Fichier requis.'}, status=400)
    try:
        import cloudinary.uploader
        result = cloudinary.uploader.upload(fichier, folder='metamorphose/partenaires', resource_type='image')
        return Response({'url': result.get('secure_url','')})
    except Exception as e:
        return Response({'detail': str(e)}, status=500)
