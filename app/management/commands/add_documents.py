from django.core.management.base import BaseCommand

from app.models import TenderDocument
from app.parsers.ungm import UNGMWorker


class Command(BaseCommand):
    help = "Adds documents where missing for each TenderDocument object"

    def handle(self, *args, **options):

        tender_docs = TenderDocument.objects.all()

        for doc in tender_docs:
            if not doc.document:
                self.stdout.write(self.style.SUCCESS("Downloading document %s" % doc.name))
                try:
                    UNGMWorker.download_document(doc)
                except Exception as e:
                    self.stdout.write(e)

