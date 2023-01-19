from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from app.models import Tender
from app.notifications import build_email
from app.management.commands.base.params import BaseParamsUI
from app.utils import emails_to_notify

User = get_user_model()


def send_deadline_mail(tender, days_remained, recipients):
    subject = 'Deadline alert'

    html_content = render_to_string(
        'mails/deadline_alert.html',
        {
            'tender': tender,
            'days_remained': days_remained,
            'domain': settings.BASE_URL
        }
    )

    email = build_email(subject, recipients, None, html_content)
    email.send()


class Command(BaseCommand, BaseParamsUI):
    help = 'Send deadline notifications to user if they have favorite tenders expiring in 1, 3 or 7 days'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **options):
        user = User.objects.get(id=options["user_id"])
        tenders = user.favorite_tenders.filter(
            awards=None).order_by('deadline')

        days_list = sorted(settings.DEADLINE_NOTIFICATIONS)

        self.stdout.write(self.style.SUCCESS(
            f'List of days: {days_list}'
        ))

        tender_count = 0

        for tender in tenders:
            for days in days_list:
                if (
                    timezone.now() + timedelta(days=days) >
                    tender.deadline >=
                    timezone.now() + timedelta(days=days - 1)
                ):
                    self.stdout.write(self.style.SUCCESS(
                        f'Sending notification about: {tender.title}'
                    ))
                    send_deadline_mail(tender, days, [user.email])
                    tender_count += 1
                    break

        return self.style.SUCCESS(
            f'Sent notifications about {tender_count} tenders...'
        )
