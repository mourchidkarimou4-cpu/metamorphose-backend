from rest_framework import serializers
from .models import Evenement, Ticket


class EvenementPublicSerializer(serializers.ModelSerializer):
    places_restantes = serializers.IntegerField(read_only=True)
    complet          = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Evenement
        fields = [
            'id', 'nom', 'slug', 'description', 'date', 'lieu',
            'places_total', 'places_restantes', 'complet',
            'prix', 'image', 'actif',
        ]


class EvenementAdminSerializer(serializers.ModelSerializer):
    places_restantes = serializers.IntegerField(read_only=True)
    nb_tickets       = serializers.SerializerMethodField()

    class Meta:
        model  = Evenement
        fields = '__all__'

    def get_nb_tickets(self, obj):
        return obj.tickets.filter(statut__in=['valide','scanne']).count()


class TicketSerializer(serializers.ModelSerializer):
    evenement_nom  = serializers.CharField(source='evenement.nom',  read_only=True)
    evenement_date = serializers.DateTimeField(source='evenement.date', read_only=True)
    evenement_lieu = serializers.CharField(source='evenement.lieu', read_only=True)
    nom_complet    = serializers.CharField(read_only=True)

    class Meta:
        model  = Ticket
        fields = [
            'id', 'code', 'evenement', 'evenement_nom',
            'evenement_date', 'evenement_lieu',
            'nom_complet', 'nom', 'email', 'telephone',
            'statut', 'scanne_le', 'created_at',
        ]


class ReservationSerializer(serializers.Serializer):
    evenement_id = serializers.IntegerField()
    nom          = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)
    email        = serializers.EmailField()
    telephone    = serializers.CharField(max_length=20, required=False, default='', allow_blank=True)
