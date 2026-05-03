import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Evenement, Ticket
from .serializers import (
    EvenementPublicSerializer, EvenementAdminSerializer,
    TicketSerializer, ReservationSerializer,
)

logger = logging.getLogger(__name__)


# ── PUBLIC ────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def evenements_list(request):
    """Liste des événements actifs à venir."""
    qs = Evenement.objects.filter(actif=True)
    return Response(EvenementPublicSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def evenement_detail(request, slug):
    try:
        ev = Evenement.objects.get(slug=slug, actif=True)
        return Response(EvenementPublicSerializer(ev).data)
    except Evenement.DoesNotExist:
        return Response({'detail': 'Événement introuvable.'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def reserver(request):
    """Réserver un ticket (membre connecté ou visiteur)."""
    s = ReservationSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=400)
    d = s.validated_data

    try:
        ev = Evenement.objects.get(pk=d['evenement_id'], actif=True)
    except Evenement.DoesNotExist:
        return Response({'detail': 'Événement introuvable.'}, status=404)

    if ev.complet:
        return Response({'detail': 'Cet événement est complet.'}, status=400)

    # Vérifier si l'email a déjà un ticket valide
    if Ticket.objects.filter(
        evenement=ev, email=d['email'], statut__in=['valide', 'scanne']
    ).exists():
        return Response({'detail': 'Un ticket existe déjà pour cet email.'}, status=400)

    # Créer le ticket
    user = request.user if request.user.is_authenticated else None
    nom  = d.get('nom', '') or (f"{user.first_name} {user.last_name}".strip() if user else '')
    email = d['email'] or (user.email if user else '')

    ticket = Ticket.objects.create(
        evenement=ev,
        user=user,
        nom=nom,
        email=email,
        telephone=d.get('telephone', ''),
    )

    # Email de confirmation
    try:
        _email_confirmation(ticket)
    except Exception as e:
        logger.warning(f"Email confirmation ticket non envoyé : {e}")

    return Response(TicketSerializer(ticket).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verifier_ticket(request, code):
    """Vérifier un ticket par son code UUID (pour le scan QR)."""
    try:
        ticket = Ticket.objects.select_related('evenement').get(code=code)
    except Ticket.DoesNotExist:
        return Response({'valide': False, 'detail': 'Ticket introuvable.'}, status=404)

    if ticket.statut == 'annule':
        return Response({'valide': False, 'detail': 'Ticket annulé.', 'ticket': TicketSerializer(ticket).data}, status=400)

    if ticket.statut == 'scanne':
        return Response({
            'valide': False,
            'detail': f'Ticket déjà scanné le {ticket.scanne_le.strftime("%d/%m/%Y à %Hh%M")}.',
            'ticket': TicketSerializer(ticket).data,
        }, status=400)

    return Response({'valide': True, 'ticket': TicketSerializer(ticket).data})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def scanner_ticket(request, code):
    """Scanner un ticket à l'entrée (marque comme scanné)."""
    try:
        ticket = Ticket.objects.select_related('evenement').get(code=code)
    except Ticket.DoesNotExist:
        return Response({'success': False, 'detail': 'Ticket introuvable.'}, status=404)

    if ticket.statut == 'annule':
        return Response({'success': False, 'detail': 'Ticket annulé.'}, status=400)

    if ticket.statut == 'scanne':
        return Response({
            'success': False,
            'detail': f'Déjà scanné le {ticket.scanne_le.strftime("%d/%m/%Y à %Hh%M")}.',
            'ticket': TicketSerializer(ticket).data,
        }, status=400)

    ticket.statut    = 'scanne'
    ticket.scanne_le = timezone.now()
    ticket.save(update_fields=['statut', 'scanne_le'])

    return Response({'success': True, 'ticket': TicketSerializer(ticket).data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_tickets(request):
    """Tickets du membre connecté."""
    tickets = Ticket.objects.filter(
        user=request.user
    ).select_related('evenement')
    return Response(TicketSerializer(tickets, many=True).data)


# ── ADMIN ─────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_evenements(request):
    if request.method == 'GET':
        qs = Evenement.objects.all()
        return Response(EvenementAdminSerializer(qs, many=True).data)
    s = EvenementAdminSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_evenement_detail(request, pk):
    try:
        ev = Evenement.objects.get(pk=pk)
    except Evenement.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'GET':
        return Response(EvenementAdminSerializer(ev).data)
    if request.method == 'DELETE':
        ev.delete()
        return Response(status=204)
    s = EvenementAdminSerializer(ev, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_tickets(request):
    ev_id  = request.query_params.get('evenement')
    limit  = min(int(request.query_params.get('limit',  200)), 1000)
    offset = int(request.query_params.get('offset', 0))
    qs     = Ticket.objects.select_related('evenement', 'user').all()
    if ev_id:
        qs = qs.filter(evenement_id=ev_id)
    total = qs.count()
    page  = qs[offset:offset + limit]
    return Response({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': TicketSerializer(page, many=True).data,
    })


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_ticket_detail(request, pk):
    try:
        ticket = Ticket.objects.get(pk=pk)
    except Ticket.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    s = TicketSerializer(ticket, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)


# ── Helper ─────────────────────────────────────────────────────

def _email_confirmation(ticket):
    import qrcode
    import io
    import base64
    from django.core.mail import EmailMultiAlternatives
    from django.core.mail import get_connection
    from django.conf import settings
    from email.mime.image import MIMEImage

    ev       = ticket.evenement
    date_str = ev.date.strftime("%d %B %Y à %Hh%M")
    nom      = ticket.nom_complet
    code     = str(ticket.code)

    # Générer le QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(code)
    qr.make(fit=True)
    img     = qr.make_image(fill_color="black", back_color="white")
    buf     = io.BytesIO()
    img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F0E8DA;font-family:'Montserrat',Arial,sans-serif">
  <div style="max-width:480px;margin:32px auto;background:#0A0A0A;border-radius:16px;overflow:hidden">

    <!-- Header doré -->
    <div style="background:linear-gradient(135deg,#C9A96A,#E8D5A8,#C9A96A);padding:24px;text-align:center">
      <p style="font-size:10px;letter-spacing:4px;text-transform:uppercase;color:#2A1506;margin:0 0 4px">Méta'Morph'Ose · White & Black</p>
      <p style="font-size:22px;font-weight:700;color:#0A0A0A;margin:0;font-style:italic">Brunch des Métamorphosées</p>
      <p style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#5A3A00;margin:6px 0 0">Pass d'accès officiel</p>
    </div>

    <!-- Pointillés -->
    <div style="border-top:2px dashed rgba(201,169,106,0.4);margin:0 24px"></div>

    <!-- Corps -->
    <div style="padding:24px;color:#F8F5F2">
      <p style="font-size:14px;color:rgba(248,245,242,0.6);margin:0 0 20px">Bonjour <strong style="color:#C9A96A">{nom}</strong>,<br>votre réservation est confirmée.</p>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Date</p>
          <p style="font-size:12px;color:#F8F5F2;margin:0;font-weight:500">{date_str}</p>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Lieu</p>
          <p style="font-size:12px;color:#F8F5F2;margin:0;font-weight:500">{ev.lieu or "À définir"}</p>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Titulaire</p>
          <p style="font-size:12px;color:#F8F5F2;margin:0;font-weight:500">{nom}</p>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Événement</p>
          <p style="font-size:12px;color:#F8F5F2;margin:0;font-weight:500">{ev.nom}</p>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Téléphone</p>
          <p style="font-size:12px;color:#F8F5F2;margin:0;font-weight:500">{ticket.telephone or "—"}</p>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#C9A96A;margin:0 0 3px">Montant payé</p>
          <p style="font-size:12px;color:#C9A96A;margin:0;font-weight:700">{ev.prix:,} FCFA</p>
        </div>
      </div>

      <div style="border-top:1px solid rgba(201,169,106,0.2);padding-top:20px;display:flex;align-items:center;gap:16px">
        <div style="background:#F8F5F2;border-radius:8px;padding:8px;flex-shrink:0">
          <img src="cid:qrcode" width="100" height="100" alt="QR Code" style="display:block"/>
        </div>
        <div>
          <p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#C9A96A;margin:0 0 6px">Code d'accès</p>
          <p style="font-size:9px;color:rgba(248,245,242,0.4);margin:0 0 8px;word-break:break-all;font-family:monospace">{code}</p>
          <p style="font-size:10px;color:rgba(248,245,242,0.5);margin:0;line-height:1.5">Présentez ce QR code à l'entrée.<br>Non cessible · 1 pass · 1 personne.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div style="background:rgba(194,24,91,0.15);border-top:1px solid rgba(194,24,91,0.3);padding:14px 24px;text-align:center">
      <p style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:rgba(194,24,91,0.8);margin:0">1 pass · 1 personne · non transférable</p>
    </div>
  </div>

  <p style="text-align:center;font-size:11px;color:rgba(0,0,0,0.3);margin:16px">Méta'Morph'Ose · White & Black · Cotonou, Bénin</p>
</body>
</html>"""

    text_body = (
        f"Bonjour {nom},\n\n"
        f"Votre réservation pour {ev.nom} est confirmée.\n"
        f"Date : {date_str}\n"
        f"Lieu : {ev.lieu or 'À définir'}\n"
        f"Code ticket : {code}\n\n"
        f"Présentez le QR code joint à l'entrée.\n\n"
        f"Méta'Morph'Ose · White & Black"
    )

    msg = EmailMultiAlternatives(
        subject=f"Votre pass — {ev.nom}",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[ticket.email],
    )
    msg.attach_alternative(html_body, "text/html")

    # Attacher le QR code inline
    qr_img = MIMEImage(qr_bytes)
    qr_img.add_header("Content-ID", "<qrcode>")
    qr_img.add_header("Content-Disposition", "inline", filename="pass-qrcode.png")
    msg.attach(qr_img)

    msg.send(fail_silently=True)
