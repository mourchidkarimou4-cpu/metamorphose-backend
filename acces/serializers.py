from rest_framework import serializers

class VerificationCleSerializer(serializers.Serializer):
    email = serializers.EmailField()
    cle   = serializers.CharField(max_length=12, min_length=6)

    def validate(self, data):
        from .models import CleAcces
        email = data.get('email', '').strip().lower()
        cle   = data.get('cle',   '').strip().upper()
        try:
            acces = CleAcces.objects.get(
                email__iexact=email,
                cle__iexact=cle,
                is_active=True
            )
            data['acces'] = acces
        except CleAcces.DoesNotExist:
            raise serializers.ValidationError(
                "Identifiants invalides ou acces revoque. "
                "Verifiez votre email et votre cle d'acces."
            )
        return data
