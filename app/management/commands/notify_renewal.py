from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from app.models import EmailAddress, Award
from django.template.loader import render_to_string
from django.conf import settings
from app.notifications import build_email
from django.utils import timezone
from app.management.commands.base.params import BaseParamsUI


MONTHS = settings.RENEWAL_NOTIFICATIONS


def send_renewal_mail(awards, months_remained):
    subject = 'Renewal alert'
    notifications = EmailAddress.objects.filter(notify=True)
    recipients = [notification.email for notification in notifications]

    html_content = render_to_string(
        'mails/renewal_alert.html',
        {
            'awards': awards,
            'months_remained': months_remained,
            'domain': settings.BASE_URL
        }
    )

    email = build_email(subject, recipients, None, html_content)
    email.send()


def get_awards(months):
    date = timezone.now().date() + relativedelta(months=months)

    awards = Award.objects.filter(
        renewal_notified=False,
        renewal_date__isnull=False,
        renewal_date__lte=date
    ).order_by('renewal_date')

    return awards, awards.count()


class Command(BaseCommand, BaseParamsUI):
    help = 'Send renewal notifications to all users if there are awards with an upcoming renewal date'

    def add_arguments(self, parser):
        parser.add_argument('months', nargs='?', type=int, default=MONTHS)

    def handle(self, *args, **options):
        months = options['months']

        awards, award_count = get_awards(months)
        if award_count:
            send_renewal_mail(awards, months)

        awards.update(renewal_notified=True)

        return self.style.SUCCESS(
            f'Sent notifications about {award_count} awards...'
        )
