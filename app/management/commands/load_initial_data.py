from django.core.management.base import BaseCommand
import json

from app.models import CPVCode, TedCountry, UNSPSCCode

fixtures_dir = "./app/fixtures/"
def add_cpv_codes():

    with open(fixtures_dir + "cpv_codes.json") as f:
        cpv_codes = json.load(f)
        for code in cpv_codes:
            CPVCode.objects.bulk_create([CPVCode(pk=code["pk"])])

def remove_cpv_codes():


    with open(fixtures_dir + "cpv_codes.json") as f:
        cpv_codes = json.load(f)
        for code in cpv_codes:
            CPVCode.objects.filter(pk=code["pk"]).delete()

def add_ted_countries():

    with open(fixtures_dir + "ted_countries.json") as f:
        ted_countries = json.load(f)
        for country in ted_countries:
            TedCountry.objects.bulk_create([TedCountry(pk=country["pk"])])

def remove_ted_countries():

    with open(fixtures_dir + "ted_countries.json") as f:
        ted_countries = json.load(f)
        for country in ted_countries:
            TedCountry.objects.filter(pk=country["pk"]).delete()


def add_unspsc_codes():

    with open(fixtures_dir + "unspsc_codes_software.json") as f:
        unspsc_codes = json.load(f)
        for code in unspsc_codes:
            UNSPSCCode.objects.bulk_create([UNSPSCCode(
                pk=code["pk"],
                id_ungm=code["fields"]["id_ungm"],
                name=code["fields"]["name"],
            )])


def remove_unspsc_codes():

    with open(fixtures_dir + "unspsc_codes_software.json") as f:
        unspsc_codes = json.load(f)
        for code in unspsc_codes:
            UNSPSCCode.objects.filter(pk=code["pk"]).delete()

class Command(BaseCommand):
    help = "Loads data for CPVCode, TEDCountry and UNSPSCCode models"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reverse',
            action='store_true',
            help='Delete initially loaded data for CPVCode, TEDCountry and UNSPSCCode models',
        )

    def handle(self, *args, **options):

        if options['reverse']:
            remove_cpv_codes()
            self.stdout.write(self.style.SUCCESS("Successfully deleted data for CPVCode model"))
            remove_ted_countries()
            self.stdout.write(self.style.SUCCESS("Successfully deleted data for TEDCountry model"))
            remove_unspsc_codes()
            self.stdout.write(self.style.SUCCESS("Successfully deleted data for UNSPSCCode model"))
        else:
            add_cpv_codes()
            self.stdout.write(self.style.SUCCESS("Successfully loaded data for CPVCode model"))
            add_ted_countries()
            self.stdout.write(self.style.SUCCESS("Successfully loaded data for TEDCountry model"))
            add_unspsc_codes()
            self.stdout.write(self.style.SUCCESS("Successfully loaded data for UNSPSCCode model"))
