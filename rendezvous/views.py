import logging
import threading
from datetime import date as date_type
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import RendezVous, Disponibilite

logger = logging.getLogger(__name__)

TYPES_LABELS = {
    'decouverte':   'Appel Découverte — 20 min — Gratuit',
    'coaching':     'Séance de Coaching — 60 min',
    'consultation': 'Consultation Image & Style — 45 min',
}
MODES_LABELS = {
    'en_ligne':   'En ligne (Zoom / WhatsApp)',
    'presentiel': 'En présentiel — Cotonou',
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
    pris   = set(RendezVous.objects.filter(date=d).values_list('heure', flat=True))

    creneaux = []
    for dispo in dispos:
        from datetime import datetime, timedelta
        current = datetime.combine(d, dispo.heure_debut)
        end     = datetime.combine(d, dispo.heure_fin)
        while current < end:
            h = current.time()
            creneaux.append({
                'heure':      h.strftime('%H:%M'),
                'disponible': h not in pris,
            })
            current += timedelta(minutes=30)

    return Response({'date': date_str, 'creneaux': creneaux})


# ── PRENDRE UN RDV ───────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def prendre_rdv(request):
    data     = request.data
    prenom   = data.get('prenom','').strip()
    nom      = data.get('nom','').strip()
    email    = data.get('email','').strip()
    whatsapp = data.get('whatsapp','').strip()
    pays     = data.get('pays','').strip()
    type_rdv = data.get('type_rdv','')
    mode     = data.get('mode','')
    date_str = data.get('date','')
    heure_str= data.get('heure','')
    message  = data.get('message','').strip()

    if not all([prenom, nom, email, whatsapp, type_rdv, mode, date_str, heure_str]):
        return Response({'error': 'Tous les champs obligatoires sont requis.'}, status=400)

    try:
        d = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'Date invalide.'}, status=400)

    if d < date_type.today():
        return Response({'error': 'La date doit être dans le futur.'}, status=400)

    from datetime import time as time_type
    try:
        h, m   = heure_str.split(':')
        heure  = time_type(int(h), int(m))
    except Exception:
        return Response({'error': 'Heure invalide.'}, status=400)

    if RendezVous.objects.filter(date=d, heure=heure).exists():
        return Response({'error': 'Ce créneau est déjà réservé. Veuillez en choisir un autre.'}, status=409)

    rdv = RendezVous.objects.create(
        prenom=prenom, nom=nom, email=email,
        whatsapp=whatsapp, pays=pays,
        type_rdv=type_rdv, mode=mode,
        date=d, heure=heure, message=message,
    )

    type_label = TYPES_LABELS.get(type_rdv, type_rdv)

    def envoyer_emails():
        mode_label = MODES_LABELS.get(mode, mode)
        date_fr    = d.strftime('%d/%m/%Y')
        gratuit    = rdv.est_gratuit

        # Email cliente
        try:
            msg = EmailMultiAlternatives(
                subject=f"Méta'Morph'Ose · Confirmation de votre rendez-vous",
                body=f"Bonjour {prenom},\n\nVotre rendez-vous '{type_label}' le {date_fr} à {heure_str} ({mode_label}) a bien été enregistré.\nPrélia vous contactera pour confirmer.\n\nMéta'Morph'Ose",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            html = f"""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"></head>
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
    <h2 style="font-family:Georgia,serif;font-size:18px;color:#F8F5F2;text-align:center;margin:0 0 6px;">Rendez-vous enregistré</h2>
    <p style="color:rgba(248,245,242,.45);text-align:center;font-size:13px;margin:0 0 28px;">Bonjour {prenom}, votre demande a bien été reçue.</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Type</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{type_label}</td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Mode</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{mode_label}</td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:rgba(248,245,242,.4);font-size:12px;">Date</td><td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);color:#F8F5F2;font-size:12px;text-align:right;">{date_fr}</td></tr>
      <tr><td style="padding:10px 0;color:rgba(248,245,242,.4);font-size:12px;">Heure</td><td style="padding:10px 0;color:#C9A96A;font-size:14px;font-weight:700;text-align:right;">{heure_str}</td></tr>
    </table>
    <div style="margin-top:20px;padding:14px;background:rgba(201,169,106,.05);border:1px solid rgba(201,169,106,.12);border-radius:2px;">
      <p style="color:rgba(248,245,242,.6);font-size:12px;line-height:1.7;margin:0;">
        {'Ce rendez-vous est <strong style="color:#4CAF50;">gratuit</strong>. Prélia vous contactera pour confirmer les détails.' if gratuit else 'Ce rendez-vous est payant. Prélia vous contactera pour les modalités de paiement et confirmer votre place.'}
      </p>
    </div>
  </div>
  <p style="text-align:center;font-family:Georgia,serif;font-style:italic;color:rgba(201,169,106,.3);font-size:12px;margin-top:24px;">© 2026 Méta'Morph'Ose · Prélia APEDO AHONON</p>
</div>
</body></html>"""
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=True)
        except Exception as e:
            logger.warning(f"Email RDV client non envoyé : {e}")

        # Email admin
        try:
            admin_email = settings.ADMIN_EMAIL or settings.EMAIL_HOST_USER
            if admin_email:
                send_mail(
                    subject=f"[MMO] Nouveau RDV — {prenom} {nom} · {type_label} · {date_fr} {heure_str}",
                    message=f"Nouveau rendez-vous :\n{prenom} {nom}\n{email}\n{whatsapp}\nType: {type_label}\nMode: {mode_label}\nDate: {date_fr} à {heure_str}\nMessage: {message}",
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
        'date': str(r.date), 'heure': str(r.heure)[:5],
        'statut': r.statut, 'statut_label': r.get_statut_display(),
        'message': r.message, 'note_admin': r.note_admin,
        'lien_reunion': r.lien_reunion, 'paiement_recu': r.paiement_recu,
        'est_gratuit': r.est_gratuit, 'duree': r.duree,
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

    statut      = request.data.get('statut', rdv.statut)
    note_admin  = request.data.get('note_admin', rdv.note_admin)
    lien_reunion= request.data.get('lien_reunion', rdv.lien_reunion)

    rdv.statut       = statut
    rdv.note_admin   = note_admin
    rdv.lien_reunion = lien_reunion
    rdv.save()

    # Notifier le client si confirmé ou refusé
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
