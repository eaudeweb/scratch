import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.functional import cached_property
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User

from app.exceptions import NoRecipients
from app.fields import LowerCharField

import re

from tika import parser

SOURCE_CHOICES = [
    ("UNGM", "UNGM"),
    ("TED", "TED"),
    ("IUCN", "IUCN"),
]

fields = [r"title", r"description"]


class BaseTimedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(BaseTimedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    notify = models.BooleanField(
        default=True,
        help_text="Whether this user should receive email notifications or not.",
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

    def clean(self):
        if self.notify and not self.user.email:
            raise ValidationError(
                "Notifications cannot be activated for users without an email."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Keyword(BaseTimedModel):
    value = LowerCharField(max_length=50, unique=True)

    def __str__(self):
        return "{}".format(self.value)

    @staticmethod
    def get_values_list():
        return list(Keyword.objects.values_list("value", flat=True))


def keywords_in(text):
    """Returns a list with all the keywords found in the text content"""
    keywords = Keyword.get_values_list()
    return list(set(keywords) & set(re.split(r"\W+", str(text).lower())))


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return "{}".format(self.name)


class Tender(BaseTimedModel):
    reference = models.CharField(unique=True, max_length=255)
    notice_type = models.CharField(null=True, max_length=255)
    title = models.CharField(null=True, max_length=512)
    organization = models.CharField(null=True, max_length=255)
    published = models.DateField(null=True)
    deadline = models.DateTimeField(null=True)
    description = models.TextField(null=True, blank=True, max_length=5059)
    has_keywords = models.BooleanField(default=False)
    notified = models.BooleanField(default=False)
    url = models.CharField(max_length=255)
    hidden = models.BooleanField(default=False)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    unspsc_codes = models.CharField(max_length=1024, null=True, blank=True)
    cpv_codes = models.CharField(max_length=1024, null=True, blank=True)
    seen_by = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    keywords = models.ManyToManyField(Keyword, related_name="tenders", blank=True)

    tags = models.ManyToManyField(Tag, blank=True)
    followers = models.ManyToManyField(
        User,
        through="Favorite",
        through_fields=("tender", "follower"),
        related_name="favorite_tenders",
    )

    def __str__(self):
        return "{}".format(self.title)

    @property
    def safe_id(self):
        """
        When USE_THOUSAND_SEPARATOR=True, Djando templates render ids with
        commas (e.g. `1,000`). This can break CSS selectors and any Javascript
        code that relies on it. This property returns a safe id string with no
        commas.
        """
        return str(self.id)

    @cached_property
    def marked_keyword_title(self):
        keywords = Keyword.get_values_list()
        title = self.title or ""
        if not keywords:
            return title

        regex = r"(" + r"|".join(keywords) + r")"
        return re.sub(regex, r"<mark>\1</mark>", title, flags=re.IGNORECASE)

    @cached_property
    def marked_keyword_description(self):
        keywords = Keyword.get_values_list()
        description = self.description or ""
        if not keywords:
            return description

        regex = r"(" + r"|".join(keywords) + r")"
        return re.sub(regex, r"<mark>\1</mark>", description, flags=re.IGNORECASE)

    def find_keywords(self, fields):
        """
        Return queryset with all Keyword objects whose value was found in the
        text of any of the fields.
        """
        found_keywords = []

        for field in fields:
            field_content = getattr(self, field)
            found_keywords += keywords_in(field_content)

        return Keyword.objects.filter(value__in=found_keywords)

    def is_favorite_of(self, user):
        return self.followers.filter(id=user.id).exists()

    def save(self, *args, **kwargs):
        keywords = list(self.find_keywords(fields))
        if keywords:
            self.has_keywords = True
        super().save(*args, **kwargs)
        self.keywords.set(keywords)


class Favorite(BaseTimedModel):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites_where_follower"
    )
    inviter = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="favorites_where_inviter",
    )

    class Meta:
        unique_together = ["tender", "follower"]

    def __str__(self) -> str:
        return (
            f'Relation between tender "#{self.tender_id} ({self.tender.title[:5]}...)" '
            f'and follower "{self.follower.username}"'
        )


class Vendor(BaseTimedModel):
    name = models.CharField(null=False, blank=False, max_length=255)
    email = models.EmailField(null=True, blank=True)
    contact_name = models.CharField(null=True, blank=True, max_length=255)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}".format(self.name)

    def get_absolute_url(self):
        return reverse("vendor_detail_view", kwargs={"pk": self.pk})


class Award(BaseTimedModel):
    value = models.FloatField(null=True)
    currency = models.CharField(null=True, max_length=3)
    award_date = models.DateField()
    renewal_date = models.DateField(null=True)
    notified = models.BooleanField(default=False)
    renewal_notified = models.BooleanField(default=False)
    # TODO: Investigate whether this coould be refactored to a OneToOneField
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="awards")
    vendors = models.ManyToManyField("Vendor", related_name="awards")

    def __str__(self):
        return "{} WON BY {}".format(self.tender.title, self.get_vendors)

    @property
    def get_vendors(self):
        return ",".join(self.vendors.values_list("name", flat=True))

    get_vendors.fget.short_description = "Vendors names"

    def convert_value_to_string(self):
        return str(self.value)


class TenderDocument(BaseTimedModel):
    name = models.CharField(null=True, max_length=255)
    download_url = models.CharField(max_length=255)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    document = models.FileField(upload_to="documents", max_length=300)

    def content(self):
        try:
            parsed = parser.from_file(self.document.path)
            return parsed["content"]
        except (ValueError, FileNotFoundError) as e:
            logging.warning(e)
            pass

    class Meta:
        unique_together = (
            "name",
            "tender",
        )


class WorkerLog(BaseTimedModel):
    update = models.DateField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    tenders_count = models.IntegerField()

    def __str__(self):
        return "{}".format(self.update)


class Email(BaseTimedModel):
    subject = models.CharField(max_length=255, blank=True, null=False)
    from_email = models.CharField(max_length=255)
    to = ArrayField(models.CharField(max_length=255))
    cc = ArrayField(models.CharField(max_length=255, blank=True), null=True)
    body = models.TextField(blank=True, null=True)

    def send(self):
        if not self.to:
            raise NoRecipients("No recipients found.")
        text_content = strip_tags(self.body)

        email = EmailMultiAlternatives(
            subject=self.subject,
            from_email=self.from_email,
            to=self.to,
            cc=self.cc,
            body=text_content,
        )

        email.attach_alternative(self.body, "text/html")
        email.send()

    def __str__(self):
        return "Email '%s' sent." % self.subject


def last_update(source):
    worker_log = WorkerLog.objects.filter(source=source).order_by("-update").first()
    return worker_log.update if worker_log else None


def set_notified(tender_or_award):
    tender_or_award.notified = True
    tender_or_award.save()


class UNSPSCCode(BaseTimedModel):
    id = models.CharField(max_length=1024, primary_key=True)
    id_ungm = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024)

    class Meta:
        verbose_name = "UNSPC code"
        verbose_name_plural = "UNSPC codes"

    def __str__(self):
        return "{}".format(self.id)


class CPVCode(BaseTimedModel):
    code = models.CharField(max_length=1024, primary_key=True)

    class Meta:
        verbose_name = "CPV code"
        verbose_name_plural = "CPV codes"

    def __str__(self):
        return "{}".format(self.code)


class TedCountry(BaseTimedModel):
    name = models.CharField(max_length=1024, primary_key=True)

    class Meta:
        verbose_name = "TED country"
        verbose_name_plural = "TED countries"


class Task(BaseTimedModel):
    id = models.CharField(max_length=32, primary_key=True)
    args = models.CharField(max_length=255, null=True, blank=True)
    kwargs = models.CharField(max_length=255, null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True, default=None)
    stopped = models.DateTimeField(null=True, blank=True, default=None)
    status = models.CharField(
        max_length=255, null=True, blank=True, default="processing"
    )
    output = models.TextField(max_length=5055, null=True, blank=True)

    def __str__(self):
        return "task_{}".format(self.args)


class TEDReleaseCalendar(BaseTimedModel):
    oj_s = models.IntegerField(null=False)
    date = models.DateField(null=False, blank=False)

    class Meta:
        verbose_name = "TED release calendar"
        verbose_name_plural = "TED release calendar"
        ordering = ["-date"]

    @property
    def year(self):
        return str(self.date.year)

    @property
    def full_oj_s(self):
        return self.year + str(self.oj_s).zfill(5)
