import logging

from django.core.management import BaseCommand

from app.models import Vendor
from app.parsers.ted import transform_vendor_name


class Command(BaseCommand):
    help = "Transforms the names of vendors and merges vendors if they refer to the same company"

    def handle(self, *args, **options):
        vendors = Vendor.objects.all()
        for vendor in vendors:

            new_name = transform_vendor_name(vendor.name)
            vendor2 = Vendor.objects.filter(name=new_name).first()
            if vendor2 != vendor:
                self.stdout.write(self.style.SUCCESS("Old name: " + vendor.name))
                self.stdout.write(self.style.SUCCESS("New name: " + new_name))
                if vendor2:
                    if not vendor2.email:
                        vendor2.email = vendor.email
                    if not vendor2.contact_name:
                        vendor2.contact_name = vendor.contact_name
                    if not vendor2.comment:
                        vendor2.comment = vendor.comment

                    for award in vendor.awards.all():
                        vendor2.awards.add(award)

                    vendor2.save()
                    vendor.delete()

                else:
                    vendor.name = new_name
                    vendor.save()
