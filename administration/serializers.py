from rest_framework import serializers
from django.contrib.auth import get_user_model
from contenu.models import Guide, Replay, DemandeContact
from .models import SiteConfig

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name','whatsapp','pays','formule','actif','date_joined','is_active']

class AdminGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guide
        fields = '__all__'

class AdminReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replay
        fields = '__all__'

class AdminDemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeContact
        fields = '__all__'

class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = '__all__'
