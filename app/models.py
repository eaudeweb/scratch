from django.db import models

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


class WorkerLog(models.Model):
    update = models.DateField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
