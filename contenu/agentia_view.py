import logging
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)

GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
MAX_MESSAGES = 20


# ── Throttle personnalisé pour l'IA ────────────────────────────
class AgentIAThrottle(AnonRateThrottle):
    """30 requêtes par heure par IP pour l'endpoint IA."""
    rate  = '30/hour'
    scope = 'agent_ia'


# ── Vue principale ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AgentIAThrottle])
def proxy_agent_ia(request):
    """
    Proxy sécurisé entre le frontend et l'API Gemini.
    La clé API reste strictement côté serveur.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY non configurée sur le serveur.")
        return Response(
            {"detail": "Service IA temporairement indisponible."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    messages      = request.data.get("messages", [])
    system_prompt = request.data.get("system", "")

    # ── Validation des entrées ──────────────────────────────────
    if not isinstance(messages, list) or not messages:
        return Response({"detail": "Le champ messages est requis."}, status=400)

    # Tronquer l'historique pour éviter les abus
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]

    # Valider que chaque message a le bon format
    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return Response({"detail": "Rôle invalide dans messages."}, status=400)
        if not isinstance(msg.get("content", ""), str):
            return Response({"detail": "Le contenu doit être une chaîne de caractères."}, status=400)
        if len(msg.get("content", "")) > 4000:
            return Response({"detail": "Message trop long (max 4000 caractères)."}, status=400)

    # ── Conversion format → Gemini ──────────────────────────────
    contents = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}],
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.7,
        },
    }
    if system_prompt:
        payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

    # ── Appel API Gemini ────────────────────────────────────────
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return Response({
            "content": [{"type": "text", "text": text}]
        })

    except requests.exceptions.Timeout:
        logger.warning("Timeout appel Gemini API")
        return Response(
            {"detail": "L'IA met trop de temps à répondre. Réessaie dans quelques secondes."},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erreur HTTP Gemini : {e.response.status_code} — {e.response.text[:200]}")
        return Response(
            {"detail": "Erreur de communication avec l'IA."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except (KeyError, IndexError) as e:
        logger.error(f"Réponse Gemini inattendue : {e}")
        return Response(
            {"detail": "Réponse inattendue de l'IA."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        logger.error(f"Erreur inattendue agent IA : {e}")
        return Response(
            {"detail": "Erreur interne. Réessaie plus tard."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
