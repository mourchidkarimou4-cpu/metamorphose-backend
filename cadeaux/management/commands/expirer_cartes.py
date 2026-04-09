from django.core.management.base import BaseCommand
from django.utils import timezone
from cadeaux.models import CartesCadeaux


class Command(BaseCommand):
    help = "Passe au statut 'expiree' toutes les cartes dont la date d'expiration est dépassée."

    def handle(self, *args, **options):
        aujourd_hui = timezone.now().date()
        qs = CartesCadeaux.objects.filter(
            statut='payee',
            date_expiration__lt=aujourd_hui,
        )
        count = qs.update(statut='expiree')
        self.stdout.write(
            self.style.SUCCESS(f"{count} carte(s) passée(s) au statut 'expiree'.")
        )
