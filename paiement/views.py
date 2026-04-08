# paiement/views.py
# Intégration Kkiapay — paiement frontend + webhook backend

import json
import hmac
import hashlib
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from accounts.models import CustomUser

PRIX_FORMULES = {
    "F1": 65000,
    "F2": 150000,
    "F3": 250000,
    "F4": 350000,
}
LABELS_FORMULES = {
    "F1": "Live · Groupe",
    "F2": "Live · Privé",
    "F3": "Présentiel · Groupe",
    "F4": "Présentiel · Privé",
}

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def initier_paiement(request):
    formule = request.query_params.get("formule")
    if formule not in PRIX_FORMULES:
        return Response({"detail": "Formule invalide."}, status=400)
    return Response({
        "montant":       PRIX_FORMULES[formule],
        "formule":       formule,
        "formule_label": LABELS_FORMULES[formule],
        "public_key":    getattr(settings, "KKIAPAY_PUBLIC_KEY", ""),
        "sandbox":       getattr(settings, "KKIAPAY_SANDBOX", True),
    })

@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_kkiapay(request):
    secret    = getattr(settings, "KKIAPAY_PRIVATE_KEY", "")
    signature = request.headers.get("X-KKIAPAY-SIGNATURE", "")
    if signature and secret:
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return Response({"detail": "Signature invalide."}, status=400)
    status = request.data.get("status", "")
    email  = request.data.get("customer", {}).get("email", "")
    if status == "SUCCESS" and email:
        try:
            user = CustomUser.objects.get(email=email)
            user.actif = True
            user.save()
        except CustomUser.DoesNotExist:
            pass
    return Response({"status": "ok"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirmer_paiement(request):
    transaction_id = request.data.get("transaction_id")
    formule        = request.data.get("formule")
    if not transaction_id:
        return Response({"detail": "transaction_id requis."}, status=400)
    private_key = getattr(settings, "KKIAPAY_PRIVATE_KEY", "")
    try:
        res  = requests.get(
            f"https://api.kkiapay.me/api/v1/transactions/{transaction_id}/status",
            headers={"X-Private-Key": private_key},
            timeout=10,
        )
        data = res.json()
        if data.get("status") != "SUCCESS":
            return Response({"detail": "Paiement non confirmé."}, status=400)
    except Exception as e:
        return Response({"detail": f"Erreur vérification : {str(e)}"}, status=500)
    user = request.user
    user.actif = True
    if formule in PRIX_FORMULES:
        user.formule = formule
    user.save()
    return Response({"detail": "Paiement confirmé. Compte activé.", "formule": formule})
