import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Categorie, Cours
from .serializers import (
    CategorieSerializer, CoursListSerializer,
    CoursDetailSerializer, CoursAdminSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def categories_list(request):
    return Response(CategorieSerializer(Categorie.objects.all(), many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def cours_list(request):
    qs = Cours.objects.filter(actif=True)
    if cat := request.query_params.get('categorie'):
        qs = qs.filter(categorie__slug=cat)
    if semaine := request.query_params.get('semaine'):
        qs = qs.filter(semaine=semaine)
    if format_ := request.query_params.get('format'):
        qs = qs.filter(format=format_)
    if request.query_params.get('vedette'):
        qs = qs.filter(en_vedette=True)
    return Response(CoursListSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cours_detail(request, slug):
    try:
        cours = Cours.objects.get(slug=slug, actif=True)
        return Response(CoursDetailSerializer(cours).data)
    except Cours.DoesNotExist:
        return Response({'detail': 'Cours introuvable.'}, status=404)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_cours_list(request):
    if request.method == 'GET':
        return Response(CoursAdminSerializer(Cours.objects.all(), many=True).data)
    s = CoursAdminSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_cours_detail(request, pk):
    try:
        cours = Cours.objects.get(pk=pk)
    except Cours.DoesNotExist:
        return Response({'detail': 'Introuvable.'}, status=404)
    if request.method == 'GET':
        return Response(CoursAdminSerializer(cours).data)
    if request.method == 'DELETE':
        cours.delete()
        return Response(status=204)
    s = CoursAdminSerializer(cours, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_categories_list(request):
    if request.method == 'GET':
        return Response(CategorieSerializer(Categorie.objects.all(), many=True).data)
    s = CategorieSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=201)
    return Response(s.errors, status=400)
