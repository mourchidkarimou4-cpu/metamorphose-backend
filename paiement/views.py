# paiement/views.py
# Les paiements sont gérés via des liens externes configurés dans l'admin.
# Le modèle Transaction reste actif pour le suivi des accès cours (learning).

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .models import Transaction
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def liste_transactions(request):
    """Liste des transactions pour le tableau de bord admin."""
    limit  = min(int(request.query_params.get('limit', 100)), 500)
    offset = int(request.query_params.get('offset', 0))
    qs     = Transaction.objects.select_related('user').all()
    total  = qs.count()
    page   = qs[offset:offset + limit]
    return Response({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': [{
            'id':             t.id,
            'transaction_id': t.transaction_id,
            'user_email':     t.user.email if t.user else t.email_client,
            'formule':        t.formule,
            'montant':        t.montant,
            'statut':         t.statut,
            'source':         t.source,
            'created_at':     t.created_at.strftime('%d/%m/%Y %H:%M'),
        } for t in page],
    })
