from rest_framework import serializers
from .models import Categorie, Cours


class CategorieSerializer(serializers.ModelSerializer):
    nb_cours = serializers.SerializerMethodField()

    class Meta:
        model  = Categorie
        fields = ['id', 'nom', 'slug', 'icone', 'couleur', 'ordre', 'nb_cours']

    def get_nb_cours(self, obj):
        return obj.cours.filter(actif=True).count()


class CoursListSerializer(serializers.ModelSerializer):
    categorie_nom    = serializers.CharField(source='categorie.nom', read_only=True)
    categorie_couleur= serializers.CharField(source='categorie.couleur', read_only=True)

    class Meta:
        model  = Cours
        fields = [
            'id', 'titre', 'slug', 'description', 'format', 'duree',
            'niveau', 'image', 'en_vedette', 'semaine',
            'categorie_nom', 'categorie_couleur', 'ordre',
        ]


class CoursDetailSerializer(serializers.ModelSerializer):
    categorie = CategorieSerializer(read_only=True)

    class Meta:
        model  = Cours
        fields = [
            'id', 'titre', 'slug', 'description', 'categorie', 'semaine',
            'format', 'contenu', 'video_url', 'audio_url', 'pdf_url',
            'duree', 'niveau', 'image', 'en_vedette', 'ordre', 'created_at',
        ]


class CoursAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Cours
        fields = '__all__'
