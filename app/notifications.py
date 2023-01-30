from django.conf import settings
from django.template.loader import render_to_string

from app.models import Email, set_notified
from app.utils import emails_to_notify


def build_email(subject, recipients, cc, body):
    sender = settings.EMAIL_SENDER

    return Email(
        subject=subject,
        from_email=sender,
        to=recipients,
        cc=cc,
        body=body
    )


def send_tenders_email(tenders, digest):
    subject = 'New tenders available' if digest else 'New tender available'
    recipients = emails_to_notify()
    title = 'New Tenders'

    if digest:
        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': tenders,
                'title': title,
                'domain': settings.BASE_URL
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

    else:
        for tender in tenders:
            html_content = render_to_string(
                'mails/new_tenders.html',
                {
                    'tenders': [tender],
                    'title': title,
                    'domain': settings.BASE_URL
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

    tenders.update(notified=True)


def send_awards_email(awards, digest):
    subject = 'New award granted' if digest else 'New awards granted'
    recipients = emails_to_notify()
    title = 'New Contract Awards'

    if digest:
        html_content = render_to_string(
            'mails/new_awards.html',
            {
                'awards': awards,
                'title': title,
                'domain': settings.BASE_URL
            }
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        awards.update(notified=True)

    else:
        for award in awards:
            html_content = render_to_string(
                'mails/new_awards.html',
                {
                    'awards': [award],
                    'title': title,
                    'domain': settings.BASE_URL
                }
            )

            email = build_email(subject, recipients, None, html_content)
            email.send()

            set_notified(award)


def send_error_email(error):
    subject = 'An error occurred while parsing new tenders'
    recipients = emails_to_notify()
    title = 'An error occurred while parsing new tenders'

    html_content = render_to_string(
        'mails/error.html',
        {
            'error': error,
            'title': title,
            'domain': settings.BASE_URL
        }
    )

    email = build_email(subject, recipients, None, html_content)
    email.send()


def send_new_tender_follower_email(tender, inviter, follower):
    subject = f'{inviter} has made you a follower of tender {tender}'
    recipients = [follower]
    html_content = render_to_string(
        'mails/new_tenders.html',
        {
            'tenders': [tender],
            'title': 'New followed tenders',
            'domain': settings.BASE_URL
        }
    )

    email = build_email(subject, recipients, None, html_content)
    email.send()
