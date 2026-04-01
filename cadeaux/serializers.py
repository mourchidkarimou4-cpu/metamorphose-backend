from rest_framework import serializers
from .models import CartesCadeaux

class CartePublicSerializer(serializers.ModelSerializer):
    formule_label = serializers.CharField(source='get_formule_display', read_only=True)
    statut_label  = serializers.CharField(source='get_statut_display', read_only=True)
    class Meta:
        model  = CartesCadeaux
        fields = ['code','formule','formule_label','destinataire_nom','occasion','message_perso','statut','statut_label','date_expiration']

class CarteCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CartesCadeaux
        fields = ['formule','acheteur_nom','acheteur_email','acheteur_tel','destinataire_nom','destinataire_email','occasion','message_perso']

class CarteAdminSerializer(serializers.ModelSerializer):
    formule_label = serializers.CharField(source='get_formule_display', read_only=True)
    statut_label  = serializers.CharField(source='get_statut_display',  read_only=True)
    class Meta:
        model  = CartesCadeaux
        fields = '__all__'
