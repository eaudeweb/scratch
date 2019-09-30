from django.db.models.signals import post_save, post_delete
from django_q.tasks import async_task

from app.models import Tender

def update_all_tenders():
    tenders = Tender.objects.all()
    for tender in tenders:
        tender.save()

def set_keywords(sender, instance, **kwargs):
    async_task(update_all_tenders)
