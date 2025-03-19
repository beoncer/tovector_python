from django.core.management.base import BaseCommand
from core.models import CreditPack
from decimal import Decimal

class Command(BaseCommand):
    help = 'Sets up initial credit packs'

    def handle(self, *args, **kwargs):
        credit_packs = [
            {
                'name': 'Starter Pack',
                'credits': 100,
                'price': Decimal('9.99'),
                'free_previews': 5,
                'preview_credit_cost': Decimal('0.2'),
            },
            {
                'name': 'Professional Pack',
                'credits': 500,
                'price': Decimal('39.99'),
                'free_previews': 20,
                'preview_credit_cost': Decimal('0.2'),
            },
            {
                'name': 'Business Pack',
                'credits': 2000,
                'price': Decimal('149.99'),
                'free_previews': 100,
                'preview_credit_cost': Decimal('0.2'),
            },
            {
                'name': 'Enterprise Pack',
                'credits': 5000,
                'price': Decimal('299.99'),
                'free_previews': 250,
                'preview_credit_cost': Decimal('0.2'),
            },
        ]

        for pack_data in credit_packs:
            CreditPack.objects.get_or_create(
                name=pack_data['name'],
                defaults=pack_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created credit pack: {pack_data["name"]}')
            ) 