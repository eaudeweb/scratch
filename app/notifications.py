from django.conf import settings
from django.template.loader import render_to_string
from getenv import env

from app.models import Notification, Email, set_notified


def send_update_email(tenders, awards, digest):
    subject = 'New tenders available' if digest else 'New tender available'
    notifications = Notification.objects.all()
    recipients = [notification.email for notification in notifications]
    title = ''

    if digest:
        if tenders:
            title += 'New Tenders'
            if awards:
                title += ' and '
        if awards:
            title += 'New Contract Awards'

        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': tenders,
                'awards': awards,
                'title': title,
                'domain': env('BASE_URL')
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        for tender in tenders:
            set_notified(tender)

        for award in awards:
            set_notified(award)

    else:
        title = 'New Tenders'
        for tender in tenders:
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'tenders': [tender],
                    'title': title,
                    'domain': env('BASE_URL')
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(tender)

        for award in awards:
            title = 'New Contract Awards'
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'awards': [award],
                    'title': title,
                    'domain': env('BASE_URL')
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(award)


def send_error_email(error):
    subject = 'An error occurred while parsing new tenders'
    notifications = Notification.objects.all()
    recipients = [notification.email for notification in notifications]
    title = 'An error occurred while parsing new tenders'

    html_content = render_to_string(
        'mails/error.html',
        {
            'error': error,
            'title': title,
            'domain': env('BASE_URL')
        }
    )

    email = build_email(subject, recipients, None, html_content)
    email.send()


def build_email(subject, recipients, cc, body):
    sender = settings.EMAIL_SENDER

    return Email(
        subject=subject,
        from_email=sender,
        to=recipients,
        cc=cc,
        body=body
    )
