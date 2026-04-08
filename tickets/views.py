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
@permission_classes([AllowAny])
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
    ev_id = request.query_params.get('evenement')
    qs    = Ticket.objects.select_related('evenement', 'user').all()
    if ev_id:
        qs = qs.filter(evenement_id=ev_id)
    return Response(TicketSerializer(qs, many=True).data)


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
    from django.core.mail import send_mail
    from django.conf import settings
    ev = ticket.evenement
    date_str = ev.date.strftime("%d %B %Y à %Hh%M")
    send_mail(
        subject=f"Votre ticket — {ev.nom}",
        message=(
            f"Bonjour {ticket.nom_complet},\n\n"
            f"Votre réservation pour {ev.nom} est confirmée.\n\n"
            f"📅 Date : {date_str}\n"
            f"📍 Lieu : {ev.lieu or 'À définir'}\n"
            f"🎫 Code ticket : {ticket.code}\n\n"
            f"Présentez ce code à l'entrée. Un QR code est disponible sur votre espace membre.\n\n"
            f"Méta'Morph'Ose · White & Black"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[ticket.email],
        fail_silently=True,
    )
