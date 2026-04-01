from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email','username','password','whatsapp','pays','formule']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username', validated_data['email']),
            email=validated_data['email'],
            password=validated_data['password'],
            whatsapp=validated_data.get('whatsapp',''),
            pays=validated_data.get('pays',''),
            formule=validated_data.get('formule',''),
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','username','whatsapp','pays','formule','actif','first_name','last_name','is_staff','is_superuser']
