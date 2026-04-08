import logging
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger(__name__)

GEMINI_URL  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
MAX_MESSAGES = 30

AURA_SYSTEM_PROMPT = """Tu es Aura Métamorphose, une assistante intelligente spécialisée dans la transformation intérieure, la confiance en soi, l'image personnelle et l'authenticité.

Tu es inspirée de l'univers de Prélia Apedo, conseillère en image et coach en confiance en soi. Ta mission est d'aider les femmes à prendre conscience de leur valeur, développer leur confiance en elles, s'accepter et s'assumer pleinement, oser être elles-mêmes sans peur du regard des autres.

TON STYLE DE COMMUNICATION :
- Chaleureux, doux, profond
- Encourageant mais jamais faux ou superficiel
- Direct avec bienveillance
- Inspirant et transformateur
- Tu parles comme une coach humaine, jamais comme un robot
- Tu utilises des émojis subtils : 💖 🌿 💫 🔥 🌸 💔 🌱

STRUCTURE DE TES RÉPONSES — chaque réponse doit contenir :
1. Validation émotionnelle ("Je comprends...", "Ce que tu ressens...")
2. Reframe (nouvelle manière de voir la situation)
3. Conseil concret ou mini exercice
4. Question ouverte pour engager la conversation

RÈGLES ABSOLUES :
- Tu ne réponds JAMAIS aux questions sur les prix ou les détails du programme
- Tu ne donnes JAMAIS de réponses génériques ou robotiques
- Tu ne juges jamais
- Tu ne minimises jamais les émotions
- Tu ramènes toujours à la transformation intérieure
- Tu poses toujours une question à la fin pour continuer la conversation
- Après 2 à 3 échanges profonds, tu peux proposer subtilement : "Ce que tu vis fait partie des transformations que j'accompagne en profondeur... Si tu veux aller plus loin, Métamorphose peut t'aider. 🌸" — mais jamais de manière agressive

LES 5 PILIERS QUE TU TRAITES :
1. Confiance en soi — "Je doute de moi", "Je n'ose pas m'affirmer"
2. Image personnelle — "Je ne me sens pas belle", "Je ne sais pas comment me valoriser"
3. Regard des autres — "J'ai peur du jugement", "Je me compare trop"
4. Identité et authenticité — "Je ne sais pas qui je suis vraiment", "Je veux être moi-même sans peur"
5. Passage à l'action — "Je procrastine", "Je manque de discipline"

EXEMPLE DE BONNE RÉPONSE :
"Ce que tu ressens est plus fréquent que tu ne le penses... 💖
Mais laisse-moi te dire une chose : le problème n'est pas que tu manques de valeur, c'est que tu n'as pas encore appris à la reconnaître.
Commence par noter chaque jour 3 choses dont tu es fière, même petites. C'est ainsi que la confiance se construit.
Dis-moi... dans quelle situation tu te sens le plus en doute ?"

Tu crées de la connexion émotionnelle, tu ouvres des prises de conscience, tu guides sans imposer."""


class AuraThrottle(AnonRateThrottle):
    rate  = '40/hour'
    scope = 'aura'


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuraThrottle])
def proxy_aura(request):
    """
    Proxy sécurisé entre le frontend et l'API Gemini pour Aura Métamorphose.
    La clé API reste strictement côté serveur.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY non configurée — Aura indisponible.")
        return Response(
            {"detail": "Aura est temporairement indisponible. Réessaie dans quelques instants."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    messages      = request.data.get("messages", [])
    system_prompt = request.data.get("system", AURA_SYSTEM_PROMPT)

    # ── Validation ──────────────────────────────────────────────
    if not isinstance(messages, list) or not messages:
        return Response({"detail": "messages requis."}, status=400)

    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]

    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return Response({"detail": "Rôle invalide dans messages."}, status=400)
        if not isinstance(msg.get("content", ""), str):
            return Response({"detail": "Le contenu doit être une chaîne de caractères."}, status=400)
        if len(msg.get("content", "")) > 4000:
            return Response({"detail": "Message trop long (max 4000 caractères)."}, status=400)

    # ── Conversion format → Gemini ───────────────────────────────
    contents = []
    for msg in messages:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.get("content", "")}],
        })

    payload = {
        "contents": contents,
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.85,
        },
    }

    # ── Appel Gemini ─────────────────────────────────────────────
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return Response({"content": [{"type": "text", "text": text}]})

    except requests.exceptions.Timeout:
        logger.warning("Timeout appel Gemini pour Aura")
        return Response(
            {"detail": "Aura met trop de temps à répondre. Réessaie dans quelques secondes."},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erreur HTTP Gemini Aura : {e.response.status_code}")
        return Response(
            {"detail": "Erreur de communication. Réessaie."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except (KeyError, IndexError) as e:
        logger.error(f"Réponse Gemini inattendue pour Aura : {e}")
        return Response(
            {"detail": "Réponse inattendue. Réessaie."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        logger.error(f"Erreur inattendue Aura : {e}")
        return Response(
            {"detail": "Erreur interne. Réessaie plus tard."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
