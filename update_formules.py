"""
Script de mise à jour des formules en base de données.
Exécuter avec : python manage.py shell < update_formules.py
"""
from administration.models import SiteConfig

updates = {
    'f1_label': 'ESSENTIELLE',
    'f1_prix':  '70 000',
    'f2_label': 'PERSONNALISÉE',
    'f2_prix':  '160 000',
    'f3_label': 'IMMERSION',
    'f3_prix':  '267 000',
    'f4_label': 'VIP',
    'f4_prix':  '370 000',
}

for cle, valeur in updates.items():
    obj, created = SiteConfig.objects.update_or_create(
        cle=cle,
        defaults={'valeur': valeur, 'section': 'formules'}
    )
    print(f"{'Créé' if created else 'Mis à jour'} : {cle} = {valeur}")

print("Terminé.")
