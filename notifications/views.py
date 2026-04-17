from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Notification, Conversation, Message,
    Vague, MembreVague, Progression,
    FormulaireSatisfaction, SessionAgenda
)
import logging

logger = logging.getLogger(__name__)
User   = get_user_model()


# ══════════════════════════════════════════════════════════════════
# 1. NOTIFICATIONS ADMIN
# ══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_notifications(request):
    limit  = int(request.query_params.get('limit', 20))
    non_lu = request.query_params.get('non_lu')
    qs     = Notification.objects.all()
    if non_lu == '1':
        qs = qs.filter(lu=False)
    notifs = qs[:limit]
    return Response({
        'total_non_lu': Notification.objects.filter(lu=False).count(),
        'results': [{
            'id':         n.id,
            'type':       n.type,
            'titre':      n.titre,
            'message':    n.message,
            'lien':       n.lien,
            'lu':         n.lu,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
            'user_email': n.user.email if n.user else '',
        } for n in notifs]
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def marquer_lu(request, pk=None):
    """Marquer une ou toutes les notifications comme lues."""
    if pk:
        Notification.objects.filter(pk=pk).update(lu=True)
    else:
        Notification.objects.filter(lu=False).update(lu=True)
    return Response({'detail': 'OK'})


def creer_notification(type_, titre, message, user=None, lien=''):
    """Utilitaire — créer une notif admin depuis n'importe quelle vue."""
    try:
        Notification.objects.create(
            type=type_, titre=titre, message=message,
            user=user, lien=lien
        )
    except Exception as e:
        logger.error(f"Notification error: {e}")


# ══════════════════════════════════════════════════════════════════
# 2. MESSAGERIE INTERNE
# ══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_conversations(request):
    """Liste toutes les conversations (vue admin)."""
    convs = Conversation.objects.select_related('membre').all()
    return Response([{
        'id':             c.id,
        'membre_email':   c.membre.email,
        'membre_prenom':  c.membre.first_name,
        'non_lu_admin':   c.non_lu_admin,
        'non_lu_membre':  c.non_lu_membre,
        'updated_at':     c.updated_at.strftime('%d/%m/%Y %H:%M'),
        'dernier_message': c.messages.last().contenu[:60] if c.messages.exists() else '',
    } for c in convs])


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def messages_conversation(request, membre_id=None):
    """
    GET  → lire les messages d'une conversation
    POST → envoyer un message
    Admin peut accéder à n'importe quel membre_id.
    Membre accède uniquement à sa propre conversation.
    """
    if request.user.is_staff:
        try:
            membre = User.objects.get(pk=membre_id)
        except User.DoesNotExist:
            return Response({'detail': 'Membre introuvable.'}, status=404)
    else:
        membre = request.user

    conv, _ = Conversation.objects.get_or_create(membre=membre)

    if request.method == 'GET':
        # Marquer comme lus côté lecteur
        if request.user.is_staff:
            conv.non_lu_admin = 0
            conv.save()
            conv.messages.filter(est_admin=False, lu=False).update(lu=True)
        else:
            conv.non_lu_membre = 0
            conv.save()
            conv.messages.filter(est_admin=True, lu=False).update(lu=True)

        msgs = conv.messages.select_related('expediteur').all()
        return Response([{
            'id':         m.id,
            'contenu':    m.contenu,
            'est_admin':  m.est_admin,
            'expediteur': m.expediteur.first_name or m.expediteur.email,
            'lu':         m.lu,
            'created_at': m.created_at.strftime('%d/%m/%Y %H:%M'),
        } for m in msgs])

    # POST — envoyer message
    contenu = request.data.get('contenu', '').strip()
    if not contenu:
        return Response({'detail': 'Message vide.'}, status=400)

    est_admin = request.user.is_staff
    msg = Message.objects.create(
        conversation=conv,
        expediteur=request.user,
        contenu=contenu,
        est_admin=est_admin,
    )

    # Mettre à jour compteurs non lus
    if est_admin:
        conv.non_lu_membre += 1
    else:
        conv.non_lu_admin += 1
    conv.save()

    # Notif admin si message d'un membre
    if not est_admin:
        creer_notification(
            'message',
            f"Nouveau message de {membre.first_name or membre.email}",
            contenu[:100],
            user=membre,
            lien=f'/admin?tab=messagerie&membre={membre.pk}'
        )

    return Response({
        'id':         msg.id,
        'contenu':    msg.contenu,
        'est_admin':  msg.est_admin,
        'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M'),
    }, status=201)


# ══════════════════════════════════════════════════════════════════
# 3. PLANIFICATEUR DE VAGUES
# ══════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def vagues_list(request):
    if request.method == 'GET':
        vagues = Vague.objects.prefetch_related('membres').all()
        return Response([{
            'id':               v.id,
            'nom':              v.nom,
            'numero':           v.numero,
            'date_debut':       v.date_debut.strftime('%Y-%m-%d'),
            'date_fin':         v.date_fin.strftime('%Y-%m-%d'),
            'statut':           v.statut,
            'places_max':       v.places_max,
            'places_prises':    v.places_prises,
            'places_restantes': v.places_restantes,
            'description':      v.description,
        } for v in vagues])

    # POST — créer une vague
    data = request.data
    vague = Vague.objects.create(
        nom=data.get('nom', ''),
        numero=data.get('numero', 1),
        date_debut=data['date_debut'],
        date_fin=data['date_fin'],
        statut=data.get('statut', 'planifiee'),
        places_max=data.get('places_max', 30),
        description=data.get('description', ''),
    )
    return Response({'id': vague.id, 'nom': vague.nom}, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def vague_detail(request, pk):
    try:
        vague = Vague.objects.get(pk=pk)
    except Vague.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)

    if request.method == 'GET':
        membres = vague.membres.select_related('membre').all()
        return Response({
            'id':               vague.id,
            'nom':              vague.nom,
            'numero':           vague.numero,
            'date_debut':       vague.date_debut.strftime('%Y-%m-%d'),
            'date_fin':         vague.date_fin.strftime('%Y-%m-%d'),
            'statut':           vague.statut,
            'places_max':       vague.places_max,
            'places_prises':    vague.places_prises,
            'places_restantes': vague.places_restantes,
            'description':      vague.description,
            'membres': [{
                'id':     m.membre.id,
                'email':  m.membre.email,
                'prenom': m.membre.first_name,
                'notes':  m.notes,
                'date_ajout': m.date_ajout.strftime('%d/%m/%Y'),
            } for m in membres],
        })

    if request.method == 'PATCH':
        for field in ['nom', 'date_debut', 'date_fin', 'statut', 'places_max', 'description']:
            if field in request.data:
                setattr(vague, field, request.data[field])
        vague.save()
        return Response({'detail': 'Mis à jour.'})

    vague.delete()
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def ajouter_membre_vague(request, pk):
    try:
        vague = Vague.objects.get(pk=pk)
    except Vague.DoesNotExist:
        return Response({'detail': 'Vague introuvable.'}, status=404)

    email = request.data.get('email', '').strip()
    try:
        membre = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Membre introuvable.'}, status=404)

    mv, created = MembreVague.objects.get_or_create(
        vague=vague, membre=membre,
        defaults={'notes': request.data.get('notes', '')}
    )
    if not created:
        return Response({'detail': 'Déjà dans cette vague.'}, status=400)

    # Envoyer email de bienvenue dans la vague
    _email_vague(membre, vague)

    return Response({'detail': f'{membre.email} ajouté à Vague {vague.numero}.'}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def retirer_membre_vague(request, pk, membre_id):
    MembreVague.objects.filter(vague_id=pk, membre_id=membre_id).delete()
    return Response(status=204)


def _email_vague(membre, vague):
    try:
        send_mail(
            subject=f"Méta'Morph'Ose — Vague {vague.numero} : {vague.nom}",
            message=f"""Bonjour {membre.first_name or membre.email},

Vous êtes inscrite à la Vague {vague.numero} — {vague.nom} du programme Méta'Morph'Ose.

📅 Début : {vague.date_debut.strftime('%d %B %Y')}
📅 Fin   : {vague.date_fin.strftime('%d %B %Y')}

{vague.description}

Nous avons hâte de vous accompagner dans cette transformation.

Avec amour,
Prélia APEDO AHONON
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membre.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Email vague error: {e}")


# ══════════════════════════════════════════════════════════════════
# 4. PROGRESSION MEMBRE
# ══════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ma_progression(request):
    prog, _ = Progression.objects.get_or_create(
        membre=request.user,
        defaults={'sessions_total': 16}
    )
    return Response({
        'semaine_actuelle':     prog.semaine_actuelle,
        'sessions_completees':  prog.sessions_completees,
        'sessions_total':       prog.sessions_total,
        'pourcentage':          prog.pourcentage,
        'badges':               prog.badges,
        'notes_coach':          prog.notes_coach,
        'objectifs':            prog.objectifs,
        'updated_at':           prog.updated_at.strftime('%d/%m/%Y'),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def progression_admin(request):
    """Liste la progression de tous les membres."""
    progs = Progression.objects.select_related('membre').all()
    return Response([{
        'membre_email':        p.membre.email,
        'membre_prenom':       p.membre.first_name,
        'semaine_actuelle':    p.semaine_actuelle,
        'sessions_completees': p.sessions_completees,
        'sessions_total':      p.sessions_total,
        'pourcentage':         p.pourcentage,
        'badges':              p.badges,
        'notes_coach':         p.notes_coach,
    } for p in progs])


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_progression(request, membre_id):
    try:
        membre = User.objects.get(pk=membre_id)
    except User.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)

    prog, _ = Progression.objects.get_or_create(membre=membre)
    for field in ['semaine_actuelle', 'sessions_completees', 'sessions_total', 'notes_coach', 'objectifs']:
        if field in request.data:
            setattr(prog, field, request.data[field])
    prog.save()
    return Response({'pourcentage': prog.pourcentage, 'badges': prog.badges})


# ══════════════════════════════════════════════════════════════════
# 5. FORMULAIRE SATISFACTION J+30
# ══════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mon_formulaire_satisfaction(request):
    fs, created = FormulaireSatisfaction.objects.get_or_create(membre=request.user)

    if request.method == 'GET':
        return Response({
            'envoye':      bool(fs.envoye_le),
            'complete':    bool(fs.complete_le),
            'note_globale': fs.note_globale,
            'note_coach':   fs.note_coach,
            'note_contenu': fs.note_contenu,
            'note_transformation': fs.note_transformation,
            'recommanderait': fs.recommanderait,
        })

    # POST — soumettre le formulaire
    if fs.complete_le:
        return Response({'detail': 'Formulaire déjà complété.'}, status=400)

    for field in ['note_globale','note_coach','note_contenu','note_transformation',
                  'point_fort','point_ameliorer','recommanderait','commentaire_libre']:
        if field in request.data:
            setattr(fs, field, request.data[field])
    fs.complete_le = timezone.now()
    fs.save()

    # Notifier Prélia
    creer_notification(
        'satisfaction',
        f"Formulaire satisfaction complété — {request.user.first_name or request.user.email}",
        f"Note globale : {fs.note_globale}/10 — Recommande : {'Oui' if fs.recommanderait else 'Non'}",
        user=request.user,
        lien='/admin?tab=satisfaction'
    )

    return Response({'detail': 'Merci pour votre retour !'})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def satisfactions_admin(request):
    fs_list = FormulaireSatisfaction.objects.select_related('membre').filter(complete_le__isnull=False)
    return Response([{
        'membre_email':       f.membre.email,
        'membre_prenom':      f.membre.first_name,
        'complete_le':        f.complete_le.strftime('%d/%m/%Y') if f.complete_le else '',
        'note_globale':       f.note_globale,
        'note_coach':         f.note_coach,
        'note_contenu':       f.note_contenu,
        'note_transformation':f.note_transformation,
        'recommanderait':     f.recommanderait,
        'point_fort':         f.point_fort,
        'point_ameliorer':    f.point_ameliorer,
        'commentaire_libre':  f.commentaire_libre,
    } for f in fs_list])


@api_view(['POST'])
@permission_classes([IsAdminUser])
def envoyer_formulaire_satisfaction(request):
    """Déclencher manuellement l'envoi du formulaire à un ou tous les membres."""
    email = request.data.get('email')
    if email:
        membres = User.objects.filter(email=email, actif=True)
    else:
        membres = User.objects.filter(actif=True, is_staff=False)

    count = 0
    for membre in membres:
        fs, created = FormulaireSatisfaction.objects.get_or_create(membre=membre)
        if not fs.envoye_le:
            fs.envoye_le = timezone.now()
            fs.save()
            _email_satisfaction(membre)
            count += 1

    return Response({'detail': f'{count} formulaire(s) envoyé(s).'})


def _email_satisfaction(membre):
    try:
        lien = f"https://metamorphose-frontend.vercel.app/satisfaction"
        send_mail(
            subject="Méta'Morph'Ose — Partagez votre expérience 💛",
            message=f"""Bonjour {membre.first_name or 'chère Métamorphosée'},

Un mois s'est écoulé depuis votre parcours Méta'Morph'Ose.

Comment allez-vous ? Votre avis compte énormément pour nous et pour améliorer l'expérience des prochaines Métamorphosées.

👉 Remplir le formulaire : {lien}

Cela ne prend que 2 minutes.

Avec amour,
Prélia APEDO AHONON
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membre.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Email satisfaction error: {e}")


# ══════════════════════════════════════════════════════════════════
# 6. AGENDA COACH
# ══════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def agenda_sessions(request):
    if request.method == 'GET':
        if request.user.is_staff:
            sessions = SessionAgenda.objects.all()
        else:
            sessions = SessionAgenda.objects.filter(membres_invites=request.user)

        return Response([{
            'id':           s.id,
            'titre':        s.titre,
            'type_session': s.type_session,
            'date_debut':   s.date_debut.strftime('%Y-%m-%dT%H:%M'),
            'date_fin':     s.date_fin.strftime('%Y-%m-%dT%H:%M'),
            'description':  s.description,
            'lien_live':    s.lien_live,
            'nb_invites':   s.membres_invites.count(),
        } for s in sessions])

    # POST — créer une session (admin seulement)
    if not request.user.is_staff:
        return Response({'detail': 'Non autorisé.'}, status=403)

    data = request.data
    session = SessionAgenda.objects.create(
        titre=data.get('titre', ''),
        type_session=data.get('type_session', 'autre'),
        date_debut=data['date_debut'],
        date_fin=data['date_fin'],
        description=data.get('description', ''),
        lien_live=data.get('lien_live', ''),
    )

    # Inviter des membres
    emails_invites = data.get('membres_invites', [])
    if emails_invites:
        membres = User.objects.filter(email__in=emails_invites)
        session.membres_invites.set(membres)
        # Envoyer invitations email
        for membre in membres:
            _email_session(membre, session)

    return Response({'id': session.id, 'titre': session.titre}, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def agenda_session_detail(request, pk):
    try:
        session = SessionAgenda.objects.get(pk=pk)
    except SessionAgenda.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)

    if request.method == 'DELETE':
        session.delete()
        return Response(status=204)

    for field in ['titre', 'type_session', 'date_debut', 'date_fin', 'description', 'lien_live']:
        if field in request.data:
            setattr(session, field, request.data[field])
    session.save()
    return Response({'detail': 'Mis à jour.'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def envoyer_rappel_session(request, pk):
    """Envoyer un rappel manuel pour une session."""
    try:
        session = SessionAgenda.objects.get(pk=pk)
    except SessionAgenda.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)

    for membre in session.membres_invites.all():
        _email_rappel(membre, session)

    session.rappel_envoye = True
    session.save()
    return Response({'detail': f'Rappels envoyés à {session.membres_invites.count()} membre(s).'})


def _email_session(membre, session):
    try:
        send_mail(
            subject=f"Méta'Morph'Ose — Invitation : {session.titre}",
            message=f"""Bonjour {membre.first_name or 'chère Métamorphosée'},

Vous êtes invitée à la session suivante :

📌 {session.titre}
📅 {session.date_debut.strftime('%d %B %Y à %H:%M')}
⏱ Fin : {session.date_fin.strftime('%H:%M')}
{f'🔗 Lien : {session.lien_live}' if session.lien_live else ''}

{session.description}

À très bientôt,
Prélia APEDO AHONON
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membre.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Email session error: {e}")


def _email_rappel(membre, session):
    try:
        send_mail(
            subject=f"Rappel — {session.titre} demain",
            message=f"""Bonjour {membre.first_name or 'chère Métamorphosée'},

Rappel : votre session a lieu demain !

📌 {session.titre}
📅 {session.date_debut.strftime('%d %B %Y à %H:%M')}
{f'🔗 Lien : {session.lien_live}' if session.lien_live else ''}

À demain,
Prélia APEDO AHONON
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[membre.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Email rappel error: {e}")
