from rest_framework import serializers
from .models import Guide, Replay

class GuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guide
        fields = ['id','titre','numero','fichier']

class ReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replay
        fields = ['id','titre','semaine','video_url']
