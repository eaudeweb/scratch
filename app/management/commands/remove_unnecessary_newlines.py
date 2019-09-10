from django.core.management.base import BaseCommand, CommandError
from app.management.commands.base.params import BaseParamsUI
from app.models import Winner


class Command(BaseCommand, BaseParamsUI):
    help = 'Removes unnecessary newlines from award vendors name'

    def handle(self, *args, **options):
        winners = Winner.objects.all()

        for winner in winners:
            winner.vendor = winner.vendor.strip()
            winner.save()

        self.stdout.write(self.style.SUCCESS('Removed unnecessary new lines'))
