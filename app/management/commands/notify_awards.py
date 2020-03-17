from django.core.management.base import BaseCommand
from app.models import Award
from app.management.commands.base.params import BaseParamsUI
from app.notifications import send_awards_email


class Command(BaseCommand, BaseParamsUI):
    help = 'Notifies all users about new contract awards'

    @staticmethod
    def get_parameters():
        return [
            {
                'name': 'digest',
                'display': 'Digest',
                'type': 'checkbox',
            },
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all awards will be notified in one email.'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Sending notifications about awards...')
        )
        digest = options['digest']
        awards = Award.objects.filter(notified=False).order_by('-award_date')
        if awards:
            send_awards_email(awards, digest)
        self.stdout.write(
            self.style.SUCCESS(
                f'Sent notifications about {awards.count()} awards...'
            )
        )
