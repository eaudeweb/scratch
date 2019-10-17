from django.core.management.base import BaseCommand
from app.management.commands.base.params import BaseParamsUI
from app.models import Vendor


class Command(BaseCommand, BaseParamsUI):
    help = 'Removes unnecessary newlines from award vendors name'

    def handle(self, *args, **options):
        vendors = Vendor.objects.all()

        for vendor in vendors:
            vendor.name = vendor.name.strip()
            vendor.save()

        self.stdout.write(self.style.SUCCESS('Removed unnecessary new lines'))
        return 'Removed unnecessary new lines'
