# paiement/views.py
# Intégration FedaPay via API REST directe

import requests
import json
import hmac
import hashlib
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from accounts.models import CustomUser

FEDAPAY_BASE    = "https://sandbox-api.fedapay.com/v1"  # sandbox — changer en prod
FEDAPAY_API_KEY = getattr(settings, "FEDAPAY_SECRET_KEY", "")

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

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initier_paiement(request):
    """Créer une transaction FedaPay et retourner le lien de paiement"""
    formule  = request.data.get("formule")
    callback = request.data.get("callback_url", "http://localhost:5173/paiement/confirmation")

    if formule not in PRIX_FORMULES:
        return Response({"detail": "Formule invalide."}, status=400)

    user   = request.user
    montant= PRIX_FORMULES[formule]
    label  = LABELS_FORMULES[formule]

    headers = {
        "Authorization": f"Bearer {FEDAPAY_API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "description":   f"Méta'Morph'Ose — {label}",
        "amount":         montant,
        "currency":      {"iso": "XOF"},
        "callback_url":   callback,
        "customer": {
            "firstname": user.first_name or user.email.split("@")[0],
            "lastname":  user.last_name  or "",
            "email":     user.email,
            "phone_number": {
                "number":  user.whatsapp or "",
                "country": "BJ",
            }
        }
    }

    try:
        res = requests.post(
            f"{FEDAPAY_BASE}/transactions",
            headers=headers,
            json=payload,
            timeout=15,
        )
        data = res.json()

        if res.status_code not in [200, 201]:
            return Response({"detail": data.get("message", "Erreur FedaPay.")}, status=400)

        transaction_id  = data["v1/transaction"]["id"]
        transaction_ref = data["v1/transaction"]["reference"]

        # Générer le lien de paiement
        token_res = requests.post(
            f"{FEDAPAY_BASE}/transactions/{transaction_id}/token",
            headers=headers,
            timeout=15,
        )
        token_data  = token_res.json()
        payment_url = token_data.get("url", "")

        return Response({
            "transaction_id":  transaction_id,
            "reference":       transaction_ref,
            "payment_url":     payment_url,
            "montant":         montant,
            "formule":         formule,
            "formule_label":   label,
        })

    except requests.exceptions.ConnectionError:
        return Response({"detail": "Impossible de contacter FedaPay. Mode sandbox non disponible en local."}, status=503)
    except Exception as e:
        return Response({"detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_fedapay(request):
    """Webhook FedaPay — confirmation de paiement"""
    secret = getattr(settings, "FEDAPAY_WEBHOOK_SECRET", "")

    # Vérifier la signature
    signature = request.headers.get("X-FEDAPAY-SIGNATURE", "")
    body       = request.body
    expected   = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if signature and secret and not hmac.compare_digest(signature, expected):
        return Response({"detail": "Signature invalide."}, status=400)

    data   = json.loads(body)
    event  = data.get("name", "")
    entity = data.get("entity", {})

    if event == "transaction.approved":
        ref   = entity.get("reference", "")
        email = entity.get("customer", {}).get("email", "")
        # Activer le compte membre
        try:
            user = CustomUser.objects.get(email=email)
            user.actif = True
            user.save()
        except CustomUser.DoesNotExist:
            pass

    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def statut_paiement(request, transaction_id):
    """Vérifier le statut d'une transaction"""
    headers = {"Authorization": f"Bearer {FEDAPAY_API_KEY}"}
    try:
        res  = requests.get(f"{FEDAPAY_BASE}/transactions/{transaction_id}", headers=headers, timeout=10)
        data = res.json()
        statut = data.get("v1/transaction", {}).get("status", "unknown")
        return Response({"statut": statut, "transaction_id": transaction_id})
    except Exception as e:
        return Response({"detail": str(e)}, status=500)
