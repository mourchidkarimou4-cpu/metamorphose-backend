from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ['email', 'username', 'password', 'whatsapp', 'pays', 'formule']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value.lower()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username', validated_data['email']),
            email=validated_data['email'],
            password=validated_data['password'],
            whatsapp=validated_data.get('whatsapp', ''),
            pays=validated_data.get('pays', ''),
            formule=validated_data.get('formule', ''),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'email', 'username', 'whatsapp', 'pays',
            'formule', 'actif', 'first_name', 'last_name',
            'is_staff', 'is_superuser',
        ]


class ContactSerializer(serializers.Serializer):
    prenom   = serializers.CharField(max_length=60)
    nom      = serializers.CharField(max_length=60)
    email    = serializers.EmailField()
    whatsapp = serializers.CharField(max_length=20, required=False, default='', allow_blank=True)
    pays     = serializers.CharField(max_length=60, required=False, default='', allow_blank=True)
    formule  = serializers.ChoiceField(
        choices=['F1', 'F2', 'F3', 'F4', ''],
        required=False, default='', allow_blank=True,
    )
    message  = serializers.CharField(max_length=2000, required=False, default='', allow_blank=True)
