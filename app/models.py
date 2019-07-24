from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.utils.html import strip_tags
from django.contrib.postgres.fields import ArrayField

SOURCE_CHOICES = [
    ('UNGM', 'UNGM'),
    ('TED', 'TED'),
]


class Tender(models.Model):
    reference = models.CharField(unique=True, max_length=255)
    notice_type = models.CharField(null=True, max_length=255)
    title = models.CharField(null=True, max_length=255)
    organization = models.CharField(null=True, max_length=255)
    published = models.DateField()
    deadline = models.DateTimeField()
    description = models.TextField(null=True, max_length=5059)
    favourite = models.BooleanField(default=False)
    notified = models.BooleanField(default=False)
    url = models.CharField(max_length=255)
    hidden = models.BooleanField(default=False)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    unspsc_codes = models.CharField(max_length=1024)

    def __str__(self):
        return 'Tender list: {}'.format(self.title)


class Winner(models.Model):
    vendor = models.CharField(null=True, max_length=255)
    value = models.FloatField(null=True)
    currency = models.CharField(null=True, max_length=3)
    award_date = models.DateField()
    notified = models.BooleanField(default=False)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)

    def __str__(self):
        return '{} WON BY {}'.format(self.tender.title, self.vendor)


class TenderDocument(models.Model):
    name = models.CharField(null=True, max_length=255)
    download_url = models.CharField(max_length=255)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    # TODO see if we need unique_together


class WorkerLog(models.Model):
    update = models.DateField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)


class Email(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255, blank=True, null=False)
    from_email = models.CharField(max_length=255)
    to = ArrayField(models.CharField(max_length=255))
    cc = ArrayField(models.CharField(max_length=255, blank=True), null=True)
    body = models.TextField(blank=True, null=True)

    def send(self):
        text_content = strip_tags(self.body)

        email = EmailMultiAlternatives(
            subject=self.subject,
            from_email=self.from_email,
            to=self.to,
            cc=self.cc,
            body=text_content
        )

        email.attach_alternative(self.body, "text/html")
        email.send()

    def __str__(self):
        return "Email '%s' sent." % self.subject


class Notification(models.Model):
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return str(self.email)


def set_notified(tender_or_winner):
    tender_or_winner.notified = True
    tender_or_winner.save()
