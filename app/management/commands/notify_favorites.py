from django.contrib.auth import get_user_model
from django.core import management

from app.management.commands.base.notify import BaseNotifyCommand

User = get_user_model()


class Command(BaseNotifyCommand):
    help = 'Notifies all users about favorite tenders updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--digest',
            action='store_true',
            help='If set, all tenders will be notified in one email.'
        )

    def handle(self, *args, **options):
        users = User.objects.filter(profile__notify=True)
        for user in users:
            management.call_command(
                "notify_user_favorites", user.id, digest=options.get("digest"))
        return self.style.SUCCESS(
            'Sent notifications to all users about their favorite tenders...'
        )
