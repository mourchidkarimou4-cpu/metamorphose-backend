import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openai import OpenAI

# ── PROMPT SYSTÈME ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es Aura, l'Assistante Métamorphose. Tu es une coach émotionnelle intelligente et une guide de transformation intérieure. Tu n'es pas un robot SAV, tu ne donnes jamais de prix et tu n'expliques pas la logistique.

TON IDENTITÉ :
Ton ton est chaleureux, encourageant, profond, direct mais doux. Tu es la première expérience de Métamorphose pour l'utilisatrice. Zéro émoji dans tes réponses.

TES 5 PILIERS D'INTERVENTION :
1. Confiance en soi
2. Image personnelle
3. Regard des autres
4. Identité & Authenticité
5. Passage à l'action

ALGORITHME DE RÉPONSE OBLIGATOIRE (4 ÉTAPES) :
Tu dois structurer CHAQUE réponse selon cet algorithme :
1. Validation émotionnelle : Accueille l'émotion (ex: 'Je comprends ce que tu ressens...').
2. Reframe (Recadrage) : Apporte un mini déclic en changeant sa perception du problème.
3. Conseil / Piste concrète : Donne une petite action immédiate.
4. Question d'engagement : Termine TOUJOURS par une question ouverte pour inviter à l'approfondissement (Niveau 2 de conversation).

RÈGLES STRICTES :
- Tes messages doivent être courts, aérés et percutants. Évite absolument la surcharge de texte.
- Utilise la mémoire de la conversation pour personnaliser tes réponses (ex: 'Tu m'as dit tout à l'heure que...').
- Si l'utilisatrice atteint le Niveau 3 (Transformation), propose subtilement de rejoindre le programme Métamorphose."""

# ── CLIENT GROQ (compatible OpenAI SDK) ──────────────────────────────────────
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY manquante dans les variables d'environnement.")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


# ── VUE PRINCIPALE ────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def aura_chat(request):
    """
    POST /api/aura/chat/
    Body JSON : { "message": "...", "reset": false }
    Retourne  : { "reply": "..." }
    """

    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"]  = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Corps de la requête invalide."}, status=400)

    user_message = data.get("message", "").strip()
    reset        = data.get("reset", False)

    if not user_message:
        return JsonResponse({"error": "Le champ 'message' est requis."}, status=400)

    # ── Mémoire via session ───────────────────────────────────────────────────
    if reset or "aura_history" not in request.session:
        request.session["aura_history"] = []

    history = request.session["aura_history"]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    # ── Appel Groq ────────────────────────────────────────────────────────────
    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=400,
            temperature=0.82,
        )
        reply = completion.choices[0].message.content.strip()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Erreur Groq : {str(e)}"}, status=502)

    # ── Mise à jour historique ────────────────────────────────────────────────
    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": reply})

    if len(history) > 20:
        history = history[-20:]

    request.session["aura_history"] = history
    request.session.modified = True

    return JsonResponse({"reply": reply})


# ── VUE RESET SESSION ─────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def aura_reset(request):
    """
    POST /api/aura/reset/
    Réinitialise l'historique de la session Aura.
    """
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"]  = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    request.session["aura_history"] = []
    request.session.modified = True
    return JsonResponse({"status": "ok", "message": "Session Aura réinitialisée."})
