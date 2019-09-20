from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.utils.html import strip_tags
from django.utils.functional import cached_property
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.conf import settings

import re


SOURCE_CHOICES = [
    ('UNGM', 'UNGM'),
    ('TED', 'TED'),
]

fields = [r'title', r'description']


class Tender(models.Model):
    reference = models.CharField(unique=True, max_length=255)
    notice_type = models.CharField(null=True, max_length=255)
    title = models.CharField(null=True, max_length=255)
    organization = models.CharField(null=True, max_length=255)
    published = models.DateField(null=True)
    deadline = models.DateTimeField(null=True)
    description = models.TextField(null=True, blank=True, max_length=5059)
    favourite = models.BooleanField(default=False)
    has_keywords = models.BooleanField(default=False)
    notified = models.BooleanField(default=False)
    url = models.CharField(max_length=255)
    hidden = models.BooleanField(default=False)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    unspsc_codes = models.CharField(max_length=1024, null=True, blank=True)
    cpv_codes = models.CharField(max_length=1024, null=True, blank=True)
    seen_by = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.title)

    @cached_property
    def marked_keyword_title(self):
        keywords = Tender.get_keywords_setting()
        title = self.title or ''
        if not keywords:
            return title

        regex = r'(' + r'|'.join(keywords) + r')'
        return re.sub(regex, r'<mark>\1</mark>', title, flags=re.IGNORECASE)

    @cached_property
    def marked_keyword_description(self):
        keywords = Tender.get_keywords_setting()
        description = self.description or ''
        if not keywords:
            return description

        regex = r'(' + r'|'.join(keywords) + r')'
        return re.sub(regex, r'<mark>\1</mark>', description, flags=re.IGNORECASE)

    @staticmethod
    def check_contains(value):
        keywords = Tender.get_keywords_setting()
        return any(keyword.lower() in str(value).lower() for keyword in keywords)

    @staticmethod
    def get_keywords_setting():
        return list(Keyword.objects.values_list('value', flat=True))

    def save(self, *args, **kwargs):
        self.has_keywords = any(self.check_contains(getattr(self, field)) for field in fields)
        super().save(*args, **kwargs)


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
    document = models.FileField(upload_to='documents', max_length=300)

    class Meta:
        unique_together = ('name', 'tender',)


class WorkerLog(models.Model):
    update = models.DateField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    tenders_count = models.IntegerField()

    def __str__(self):
        return '{}'.format(self.update)


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


def last_update(source):
    worker_log = (
        WorkerLog.objects
        .filter(source=source)
        .order_by('-update')
        .first()
    )
    return worker_log.update if worker_log else None


def set_notified(tender_or_winner):
    tender_or_winner.notified = True
    tender_or_winner.save()


class UNSPSCCode(models.Model):
    id = models.CharField(max_length=1024, primary_key=True)
    id_ungm = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024)

    def __str__(self):
        return '{}'.format(self.id)


class CPVCode(models.Model):
    code = models.CharField(max_length=1024, primary_key=True)

    def __str__(self):
        return '{}'.format(self.code)


class TedCountry(models.Model):
    name = models.CharField(max_length=1024, primary_key=True)


class Task(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    args = models.CharField(max_length=255, null=True, blank=True)
    kwargs = models.CharField(max_length=255, null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True, default=None)
    stopped = models.DateTimeField(null=True, blank=True, default=None)
    status = models.CharField(max_length=255, null=True, blank=True, default="processing")
    output = models.TextField(max_length=5055, null=True, blank=True)

    def __str__(self):
        return 'task_{}'.format(self.args)


class Keyword(models.Model):
    value = models.CharField(max_length=50)

    def __str__(self):
        return '{}'.format(self.value)
