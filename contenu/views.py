from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Guide, Replay
from .serializers import GuideSerializer, ReplaySerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def guides(request):
    data = Guide.objects.filter(actif=True).order_by('numero')
    return Response(GuideSerializer(data, many=True, context={'request':request}).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def replays(request):
    formule = request.user.formule
    data = Replay.objects.filter(actif=True, formules__contains=formule).order_by('semaine')
    return Response(ReplaySerializer(data, many=True).data)
