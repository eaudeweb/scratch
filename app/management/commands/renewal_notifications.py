from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from app.models import EmailAddress, Award
from django.template.loader import render_to_string
from django.conf import settings
from app.notifications import build_email
from django.utils import timezone
from app.management.commands.base.params import BaseParamsUI


class Command(BaseCommand, BaseParamsUI):
    help = 'Send renewal notifications to all users if there are awards with an upcoming renewal date'

    def handle(self, *args, **options):
        awards = Award.objects.filter(renewal_notified=False, renewal_date__isnull=False).order_by('renewal_date')

        months = settings.RENEWAL_NOTIFICATIONS

        self.stdout.write(self.style.SUCCESS(
            f'Months: {months}'
        ))

        award_count = 0

        for award in awards:

            if timezone.now().date() + relativedelta(months=months) > award.renewal_date:
                self.stdout.write(self.style.SUCCESS(
                    f'Sending notification about: {award.tender.title}'
                ))
                self.send_renewal_mail(award, months)
                award_count += 1
                award.renewal_notified = True
                award.save()

        return self.style.SUCCESS(
            f'Sent notifications about {award_count} awards...'
        )

    @staticmethod
    def send_renewal_mail(award, months_remained):
        subject = 'Renewal alert'
        notifications = EmailAddress.objects.filter(notify=True)
        recipients = [notification.email for notification in notifications]

        html_content = render_to_string(
            'mails/renewal_alert.html',
            {
                'award': award,
                'months_remained': months_remained,
                'domain': settings.BASE_URL
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()
