from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from app.models import Tender
from app.notifications import build_email
from app.management.commands.base.params import BaseParamsUI
from app.utils import emails_to_notify


class Command(BaseCommand, BaseParamsUI):
    help = 'Send deadline notifications to all users if there are favourite tenders with 1, 3 or 7 days left'

    def handle(self, *args, **options):
        tenders = Tender.objects.filter(favourite=True, awards=None).order_by('deadline')

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
                    self.send_deadline_mail(tender, days)
                    tender_count += 1
                    break

        return self.style.SUCCESS(
            f'Sent notifications about {tender_count} tenders...'
        )

    @staticmethod
    def send_deadline_mail(tender, days_remained):
        subject = 'Deadline alert'
        recipients = emails_to_notify()

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
