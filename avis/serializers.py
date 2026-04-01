# avis/serializers.py — CORRIGÉ
from rest_framework import serializers
from .models import Temoignage

class TemoignagePublicSerializer(serializers.ModelSerializer):
    note_display    = serializers.SerializerMethodField()
    formule_display = serializers.SerializerMethodField()
    type_display    = serializers.SerializerMethodField()
    video_fichier   = serializers.SerializerMethodField()
    audio_fichier   = serializers.SerializerMethodField()
    photo_avant     = serializers.SerializerMethodField()
    photo_apres     = serializers.SerializerMethodField()

    class Meta:
        model  = Temoignage
        fields = ['id','prenom','pays','formule','formule_display','type_temo','type_display',
                  'texte','note','note_display','video_url','video_fichier','audio_fichier',
                  'photo_avant','photo_apres','en_vedette','date']

    def _abs_url(self, obj, field):
        val = getattr(obj, field, None)
        if not val: return None
        request = self.context.get('request')
        if request: return request.build_absolute_uri(val.url)
        return val.url

    def get_note_display(self, obj):
        return '★' * obj.note + '☆' * (5 - obj.note)

    def get_formule_display(self, obj):
        labels = {'F1':'Live · Groupe','F2':'Live · Privé','F3':'Présentiel · Groupe','F4':'Présentiel · Privé'}
        return labels.get(obj.formule, '')

    def get_type_display(self, obj):
        labels = {'texte':'Texte','video':'Vidéo','audio':'Audio'}
        return labels.get(obj.type_temo, '')

    def get_video_fichier(self, obj): return self._abs_url(obj, 'video_fichier')
    def get_audio_fichier(self, obj): return self._abs_url(obj, 'audio_fichier')
    def get_photo_avant(self, obj):   return self._abs_url(obj, 'photo_avant')
    def get_photo_apres(self, obj):   return self._abs_url(obj, 'photo_apres')

class TemoignageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Temoignage
        fields = ['prenom','pays','formule','type_temo','texte','note','video_url']

class TemoignageAdminSerializer(serializers.ModelSerializer):
    formule_display = serializers.SerializerMethodField()
    type_display    = serializers.SerializerMethodField()
    video_fichier   = serializers.SerializerMethodField()
    audio_fichier   = serializers.SerializerMethodField()
    photo_avant     = serializers.SerializerMethodField()
    photo_apres     = serializers.SerializerMethodField()

    class Meta:
        model  = Temoignage
        fields = '__all__'

    def _abs_url(self, obj, field):
        val = getattr(obj, field, None)
        if not val: return None
        request = self.context.get('request')
        if request: return request.build_absolute_uri(val.url)
        return val.url

    def get_formule_display(self, obj):
        labels = {'F1':'Live · Groupe','F2':'Live · Privé','F3':'Présentiel · Groupe','F4':'Présentiel · Privé'}
        return labels.get(obj.formule, '')

    def get_type_display(self, obj):
        labels = {'texte':'Texte','video':'Vidéo','audio':'Audio'}
        return labels.get(obj.type_temo, '')

    def get_video_fichier(self, obj): return self._abs_url(obj, 'video_fichier')
    def get_audio_fichier(self, obj): return self._abs_url(obj, 'audio_fichier')
    def get_photo_avant(self, obj):   return self._abs_url(obj, 'photo_avant')
    def get_photo_apres(self, obj):   return self._abs_url(obj, 'photo_apres')
