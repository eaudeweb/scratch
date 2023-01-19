from django.contrib.auth import get_user_model
from django.core import management

from app.management.commands.base.notify import BaseNotifyCommand

User = get_user_model()


class Command(BaseNotifyCommand):
    help = 'Notifies all users about favorite tenders updates'

    def handle(self, *args, **options):
        users = User.objects.filter(profile__notify=True)
        for user in users:
            management.call_command("user_deadline_notifications", user.id)
        return self.style.SUCCESS(
            'Sent deadline notifications to all users who have favorite tenders'
            ' expiring in 1, 3 or 7 days.'
        )
