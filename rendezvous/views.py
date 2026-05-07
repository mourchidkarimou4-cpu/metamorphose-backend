import logging
import threading
from datetime import date as date_type, datetime, timedelta, time as time_type
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import RendezVous, Disponibilite

logger = logging.getLogger(__name__)

TYPES_LABELS = {
    'appel_decouverte': 'Appel Découverte — 30 min — Gratuit',
    'bilan_image':      'Bilan Image — 1h',
    'seance_coaching':  'Séance de Coaching — 1h30 à 2h',
}
MODES_LABELS = {
    'en_ligne':   'En ligne',
    'presentiel': 'En présentiel — Cotonou',
}
PRIX = {
    'appel_decouverte': {'en_ligne': 0,     'presentiel': None},
    'bilan_image':      {'en_ligne': 32500,  'presentiel': 60000},
    'seance_coaching':  {'en_ligne': 40000,  'presentiel': 70000},
}
DUREES_BLOQUEES = {
    'appel_decouverte': 60,   # 30min rdv + 30min pause
    'bilan_image':      90,   # 60min rdv + 30min pause
    'seance_coaching':  150,  # 120min rdv + 30min pause
}

# ── CRÉNEAUX DISPONIBLES ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def creneaux_disponibles(request):
    date_str = request.GET.get('date', '')
    if not date_str:
        return Response({'error': 'date requis'}, status=400)
    try:
        d = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'format date invalide'}, status=400)

    jour_nom = d.strftime('%A').lower()
    JOURS_FR = {
        'monday':'lundi','tuesday':'mardi','wednesday':'mercredi',
        'thursday':'jeudi','friday':'vendredi','saturday':'samedi','sunday':'dimanche'
    }
    jour_fr = JOURS_FR.get(jour_nom, jour_nom)

    dispos = Disponibilite.objects.filter(jour=jour_fr, actif=True)

    # Calculer les créneaux bloqués par les RDV existants
    rdvs_du_jour = RendezVous.objects.filter(date=d).exclude(statut='annule')
    bloque = set()
    for rdv in rdvs_du_jour:
        debut    = datetime.combine(d, rdv.heure)
        nb_slots = DUREES_BLOQUEES.get(rdv.type_rdv, 60) // 30
        for i in range(nb_slots):
            bloque.add((debut + timedelta(minutes=30*i)).time())

    creneaux = []
    for dispo in dispos:
        current = datetime.combine(d, dispo.heure_debut)
        end     = datetime.combine(d, dispo.heure_fin)
        while current < end:
            h = current.time()
            creneaux.append({
                'heure':      h.strftime('%H:%M'),
                'disponible': h not in bloque,
            })
            current += timedelta(minutes=30)

    return Response({'date': date_str, 'creneaux': creneaux})


# ── PRENDRE UN RDV ───────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def prendre_rdv(request):
    data       = request.data
    prenom     = data.get('prenom','').strip()
    nom        = data.get('nom','').strip()
    email      = data.get('email','').strip()
    whatsapp   = data.get('whatsapp','').strip()
    pays       = data.get('pays','').strip()
    type_rdv   = data.get('type_rdv','')
    mode       = data.get('mode','')
    nb_seances = data.get('nb_seances','1')
    date_str   = data.get('date','')
    heure_str  = data.get('heure','')
    message    = data.get('message','').strip()

    if not all([prenom, nom, email, whatsapp, type_rdv, mode, date_str, heure_str]):
        return Response({'error': 'Tous les champs obligatoires sont requis.'}, status=400)

    # Appel découverte = en ligne uniquement
    if type_rdv == 'appel_decouverte' and mode != 'en_ligne':
        return Response({'error': 'L\'appel découverte est disponible en ligne uniquement.'}, status=400)

    try:
        d = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'Date invalide.'}, status=400)

    if d < date_type.today():
        return Response({'error': 'La date doit être dans le futur.'}, status=400)

    try:
        h, m  = heure_str.split(':')
        heure = time_type(int(h), int(m))
    except Exception:
        return Response({'error': 'Heure invalide.'}, status=400)

    # Vérifier que le créneau n'est pas bloqué
    rdvs_du_jour = RendezVous.objects.filter(date=d).exclude(statut='annule')
    bloque = set()
    for rdv in rdvs_du_jour:
        debut    = datetime.combine(d, rdv.heure)
        nb_slots = DUREES_BLOQUEES.get(rdv.type_rdv, 60) // 30
        for i in range(nb_slots):
            bloque.add((debut + timedelta(minutes=30*i)).time())

    if heure in bloque:
        return Response({'error': 'Ce créneau n\'est plus disponible. Veuillez en choisir un autre.'}, status=409)

    # Calculer le prix
    prix_base = PRIX.get(type_rdv, {}).get(mode, 0) or 0
    if type_rdv == 'seance_coaching' and nb_seances == '2':
        prix_total = prix_base * 2
    elif type_rdv == 'seance_coaching' and nb_seances == '3+':
        prix_total = prix_base * 3
    else:
        prix_total = prix_base

    rdv = RendezVous.objects.create(
        prenom=prenom, nom=nom, email=email,
        whatsapp=whatsapp, pays=pays,
        type_rdv=type_rdv, mode=mode,
        nb_seances=nb_seances, prix=prix_total,
        date=d, heure=heure, message=message,
    )

    type_label = TYPES_LABELS.get(type_rdv, type_rdv)
    mode_label = MODES_LABELS.get(mode, mode)

    def envoyer_emails():
        date_fr = d.strftime('%d/%m/%Y')
        gratuit = rdv.est_gratuit
        prix_str = 'Gratuit' if gratuit else f'{prix_total:,} FCFA'.replace(',',' ')

        try:
            msg = EmailMultiAlternatives(
                subject=f"Méta'Morph'Ose · Confirmation de votre rendez-vous",
                body=f"Bonjour {prenom},\n\nVotre demande de rendez-vous '{type_label}' le {date_fr} à {heure_str} ({mode_label}) a bien été enregistrée.\nPrélia vous contactera sous 24h pour confirmer.\n\nMéta'Morph'Ose",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            nb_info = f"<tr><td style=\"padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;\">Nombre de séances</td><td style=\"padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;\">{nb_seances}</td></tr>" if type_rdv == 'seance_coaching' else ""
            html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0A0A0A;font-family:'Helvetica Neue',Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;padding:40px 20px;">
  <div style="text-align:center;margin-bottom:32px;">
    <h1 style="font-family:Georgia,serif;font-size:24px;color:#F8F5F2;font-weight:400;margin:0;">
      Méta'<span style="color:#C9A96A;">Morph'</span><span style="color:#C2185B;">Ose</span>
    </h1>
  </div>
  <div style="background:#111;border:1px solid rgba(201,169,106,.2);border-radius:4px;padding:36px;">
    <div style="text-align:center;margin-bottom:24px;">
      <div style="width:56px;height:56px;border-radius:50%;background:rgba(201,169,106,.08);border:1px solid rgba(201,169,106,.3);display:inline-flex;align-items:center;justify-content:center;font-size:24px;">✓</div>
    </div>
    <h2 style="font-family:Georgia,serif;font-size:18px;color:#F8F5F2;text-align:center;margin:0 0 6px;">Demande enregistrée</h2>
    <p style="color:rgba(248,245,242,.45);text-align:center;font-size:13px;margin:0 0 28px;">Bonjour {prenom}, votre demande a bien été reçue. Prélia vous contactera sous 24h.</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Type</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{type_label}</td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Mode</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{mode_label}</td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Date</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{date_fr}</td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Heure</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#C9A96A;font-size:14px;font-weight:700;text-align:right;">{heure_str}</td></tr>
      {nb_info}
      <tr><td style="padding:10px 0;color:rgba(248,245,242,.4);font-size:12px;">Tarif</td><td style="padding:10px 0;color:{'#4CAF50' if gratuit else '#C9A96A'};font-size:13px;font-weight:700;text-align:right;">{prix_str}</td></tr>
    </table>
    {"<div style=\"margin-top:20px;padding:14px;background:rgba(76,175,80,.05);border:1px solid rgba(76,175,80,.12);border-radius:2px;\"><p style=\"color:rgba(248,245,242,.6);font-size:12px;line-height:1.7;margin:0;\">Ce rendez-vous est <strong style=\"color:#4CAF50;\">gratuit</strong>. Prélia vous contactera pour confirmer les détails.</p></div>" if gratuit else "<div style=\"margin-top:20px;padding:14px;background:rgba(201,169,106,.05);border:1px solid rgba(201,169,106,.12);border-radius:2px;\"><p style=\"color:rgba(248,245,242,.6);font-size:12px;line-height:1.7;margin:0;\">Ce rendez-vous est payant. Prélia vous contactera pour les modalités de paiement et confirmer votre place.</p></div>"}
  </div>
  <p style="text-align:center;font-family:Georgia,serif;font-style:italic;color:rgba(201,169,106,.3);font-size:12px;margin-top:24px;">© 2026 Méta'Morph'Ose · Prélia APEDO AHONON</p>
</div>
</body></html>"""
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=True)
        except Exception as e:
            logger.warning(f"Email RDV client non envoyé : {e}")

        try:
            admin_email = getattr(settings, 'ADMIN_EMAIL', None) or settings.EMAIL_HOST_USER
            if admin_email:
                nb_str = f"\nNombre de séances: {nb_seances}" if type_rdv == 'seance_coaching' else ""
                send_mail(
                    subject=f"[MMO] Nouveau RDV — {prenom} {nom} · {type_label} · {date_fr} {heure_str}",
                    message=f"Nouveau rendez-vous :\n{prenom} {nom}\n{email}\n{whatsapp}\nType: {type_label}\nMode: {mode_label}{nb_str}\nPrix: {prix_str}\nDate: {date_fr} à {heure_str}\nMessage: {message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
        except Exception as e:
            logger.warning(f"Email RDV admin non envoyé : {e}")

    threading.Thread(target=envoyer_emails, daemon=True).start()

    return Response({
        'id':      rdv.id,
        'message': 'Rendez-vous enregistré. Vous recevrez une confirmation par email.',
        'date':    date_str,
        'heure':   heure_str,
        'type':    type_label,
        'prix':    prix_total,
    }, status=201)


# ── ADMIN — LISTE RDV ────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_liste_rdv(request):
    if not request.user.is_staff:
        return Response({'error': 'Accès refusé.'}, status=403)
    statut = request.GET.get('statut', '')
    qs = RendezVous.objects.all()
    if statut:
        qs = qs.filter(statut=statut)
    data = [{
        'id': r.id, 'prenom': r.prenom, 'nom': r.nom,
        'email': r.email, 'whatsapp': r.whatsapp, 'pays': r.pays,
        'type_rdv': r.type_rdv, 'type_label': r.get_type_rdv_display(),
        'mode': r.mode, 'mode_label': r.get_mode_display(),
        'nb_seances': r.nb_seances, 'prix': r.prix,
        'date': str(r.date), 'heure': str(r.heure)[:5],
        'statut': r.statut, 'statut_label': r.get_statut_display(),
        'message': r.message, 'note_admin': r.note_admin,
        'lien_reunion': r.lien_reunion, 'paiement_recu': r.paiement_recu,
        'est_gratuit': r.est_gratuit, 'duree_rdv': r.duree_rdv,
        'created_at': r.created_at.strftime('%d/%m/%Y %H:%M'),
    } for r in qs]
    return Response(data)


# ── ADMIN — CONFIRMER / REFUSER ──────────────────────────────────
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_action_rdv(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Accès refusé.'}, status=403)
    try:
        rdv = RendezVous.objects.get(pk=pk)
    except RendezVous.DoesNotExist:
        return Response({'error': 'RDV introuvable.'}, status=404)

    statut       = request.data.get('statut', rdv.statut)
    note_admin   = request.data.get('note_admin', rdv.note_admin)
    lien_reunion = request.data.get('lien_reunion', rdv.lien_reunion)

    rdv.statut       = statut
    rdv.note_admin   = note_admin
    rdv.lien_reunion = lien_reunion
    rdv.save()

    if statut in ['confirme', 'refuse'] and rdv.email:
        def notifier():
            try:
                if statut == 'confirme':
                    sujet = "Méta'Morph'Ose · Votre rendez-vous est confirmé"
                    corps = f"Bonjour {rdv.prenom},\n\nVotre rendez-vous du {rdv.date.strftime('%d/%m/%Y')} à {str(rdv.heure)[:5]} est confirmé.\n{f'Lien de réunion : {lien_reunion}' if lien_reunion else ''}\n{note_admin}\n\nMéta'Morph'Ose"
                else:
                    sujet = "Méta'Morph'Ose · Rendez-vous non disponible"
                    corps = f"Bonjour {rdv.prenom},\n\nNous ne pouvons malheureusement pas confirmer votre rendez-vous du {rdv.date.strftime('%d/%m/%Y')}.\n{note_admin}\n\nContactez-nous sur WhatsApp pour reprogrammer.\n\nMéta'Morph'Ose"
                send_mail(sujet, corps, settings.DEFAULT_FROM_EMAIL, [rdv.email], fail_silently=True)
            except Exception as e:
                logger.warning(f"Email notification RDV : {e}")
        threading.Thread(target=notifier, daemon=True).start()

    return Response({'success': True, 'statut': statut})


# ── ADMIN — DISPONIBILITÉS ───────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_disponibilites(request):
    if not request.user.is_staff:
        return Response({'error': 'Accès refusé.'}, status=403)
    if request.method == 'GET':
        dispos = Disponibilite.objects.all()
        return Response([{
            'id': d.id, 'jour': d.jour, 'heure_debut': str(d.heure_debut)[:5],
            'heure_fin': str(d.heure_fin)[:5], 'actif': d.actif,
        } for d in dispos])
    data = request.data
    dispo = Disponibilite.objects.create(
        jour=data.get('jour'), heure_debut=data.get('heure_debut'),
        heure_fin=data.get('heure_fin'), actif=data.get('actif', True),
    )
    return Response({'id': dispo.id, 'success': True}, status=201)


@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_disponibilite_detail(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Accès refusé.'}, status=403)
    try:
        dispo = Disponibilite.objects.get(pk=pk)
    except Disponibilite.DoesNotExist:
        return Response({'error': 'Introuvable.'}, status=404)
    if request.method == 'DELETE':
        dispo.delete()
        return Response({'success': True})
    dispo.actif = request.data.get('actif', dispo.actif)
    dispo.save()
    return Response({'success': True})
