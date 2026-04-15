from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from .serializers import VerificationCleSerializer
from .models import CleAcces

class VerifierCleView(APIView):
    """
    Endpoint public — Vérifie la clé d'accès à la Communauté MMO.
    Utilisé par le formulaire React de la page Communauté.

    POST /api/acces/verifier/
    Body : { "email": "...", "cle": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerificationCleSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {
                    'acces': True,
                    'message': 'Acces autorise. Bienvenue dans la Communaute MMO.',
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'acces': False,
                'detail': 'Identifiants invalides. Verifiez votre email et votre cle d acces.',
            },
            status=status.HTTP_403_FORBIDDEN
        )


class ListeClesAdminView(APIView):
    """
    Endpoint admin — Liste toutes les clés (Coach Prélia APEDO AHONON uniquement).
    GET /api/acces/admin/cles/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        cles = CleAcces.objects.all()
        return Response([{
            'id':         c.id,
            'email':      c.email,
            'cle':        c.cle,
            'is_active':  c.is_active,
            'created_at': c.created_at.strftime('%d/%m/%Y'),
        } for c in cles])


class GenererCleAdminView(APIView):
    """
    Endpoint admin — Génère une clé pour un email donné (Coach Prélia APEDO AHONON uniquement).
    POST /api/acces/admin/generer/
    Body : { "email": "..." }
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'detail': 'Email requis.'}, status=status.HTTP_400_BAD_REQUEST)

        acces, created = CleAcces.objects.get_or_create(
            email=email,
            defaults={'is_active': True}
        )
        if not created:
            # Regénérer la clé
            acces.cle = CleAcces._generer_cle_unique()
            acces.is_active = True
            acces.save()

        return Response({
            'email':     acces.email,
            'cle':       acces.cle,
            'is_active': acces.is_active,
            'created':   created,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ToggleCleAdminView(APIView):
    """
    Endpoint admin — Active ou révoque une clé (Coach Prélia APEDO AHONON uniquement).
    PATCH /api/acces/admin/cles/<pk>/toggle/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            acces = CleAcces.objects.get(pk=pk)
        except CleAcces.DoesNotExist:
            return Response({'detail': 'Cle introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        acces.is_active = not acces.is_active
        acces.save()
        return Response({'is_active': acces.is_active})
