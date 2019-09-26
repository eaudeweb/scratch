import logging
import tarfile
import os
import time

from bs4 import BeautifulSoup, element
from datetime import date, datetime, timedelta
from django.conf import settings
from ftplib import error_perm, FTP

from django.utils.timezone import make_aware

from app.models import WorkerLog, Tender, Winner, CPVCode, TedCountry

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(levelname)s: %(message)s")


class TEDWorker:
    archives = []

    def __init__(self, last_ted_update):
        self.path = get_archives_path()
        self.last_ted_update = last_ted_update

    def ftp_download_tender_archive(self, tenders):
        ftp = self.ftp_login()

        for tender in tenders:
            if tender.published:
                ftp_path = tender.published.strftime("%Y/%m")
                ftp.cwd(f"daily-packages/{ftp_path}")
                archives = ftp.nlst()

                self.download_archive(ftp, tender.published, archives)

        ftp.quit()

    def ftp_download_latest_archives(self):
        ftp = self.ftp_login()

        last_date = self.last_ted_update or self.last_update("TED")
        last_month = last_date.strftime("%m")
        last_year = last_date.strftime("%Y")

        ftp.cwd(f"daily-packages/{last_year}/{last_month}")

        archives = ftp.nlst()
        today = date.today()

        while last_date <= today:
            self.download_archive(ftp, last_date, archives)


            last_date += timedelta(1)

            if last_year != last_date.strftime("%Y"):
                last_year = last_date.strftime("%Y")
                last_month = last_date.strftime("%m")
                ftp.cwd("../../{}/{}".format(last_year, last_month))
                archives = ftp.nlst()
            elif last_month != last_date.strftime("%m"):
                last_month = last_date.strftime("%m")
                ftp.cwd("../{}".format(last_month))
                archives = ftp.nlst()

        ftp.quit()

    def ftp_download_daily_archives(self):
        last_month = self.last_ted_update.strftime("%m")
        last_year = self.last_ted_update.strftime("%Y")

        ftp = self.ftp_login()
        ftp.cwd(f"daily-packages/{last_year}/{last_month}")

        archives = ftp.nlst()

        self.download_archive(ftp, self.last_ted_update, archives)

        ftp.quit()

    def download_archive(self, ftp, archive_date, archives):
        archive_name = self.get_archive_name(archive_date, archives)
        if archive_name:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            file_path = os.path.join(self.path, archive_name)
            with open(file_path, "wb") as f:
                ftp.retrbinary(
                    "RETR %s" % archive_name, lambda data: f.write(data)
                )
            self.archives.append(file_path)

    def parse_notices(self, tenders=[], set_notified=False):
        changed_tenders = []
        folders = []
        tenders_count = 0
        for archive_path in self.archives:
            folder_name = self.extract_data(archive_path, self.path)
            folders.append(folder_name)
            p = TEDParser(self.path, [folder_name])
            changed_tenders, added_tenders = p.parse_notices(tenders, set_notified)
            tenders_count += added_tenders
            folder_date = folder_name[:8]
            formatted_date = datetime.strptime(folder_date, "%Y%m%d").strftime("%d/%m/%Y")
            logging.warning(f"Date {formatted_date} parsed successfully")

        for archive_path in self.archives:
            os.remove(archive_path)

        for folder in folders:
            os.rmdir(os.path.join(self.path, folder))

        return changed_tenders, tenders_count

    @staticmethod
    def extract_data(archive_path, extract_path):
        tf = tarfile.open(archive_path, "r:gz")
        tf.extractall(extract_path)
        return tf.getnames()[0]

    @staticmethod
    def ftp_login():
        ftp = FTP(settings.TED_FTP_URL)
        ftp.login(user=settings.TED_FTP_USER, passwd=settings.TED_FTP_PASSWORD)
        return ftp

    @staticmethod
    def get_archive_name(last_date, archives):
        starting_name = last_date.strftime("%Y%m%d")
        for archive_name in archives:
            if archive_name.startswith(starting_name):
                return archive_name
        return None

    @staticmethod
    def add_worker_log(source, tenders_count):
        log = WorkerLog(source=source, update=date.today(), tenders_count=tenders_count)
        log.save()

    @staticmethod
    def last_update(source):
        worker_log = (
            WorkerLog.objects
                .filter(source=source)
                .order_by("-update")
                .first()
        )
        return worker_log.update if worker_log else None


class TEDParser(object):
    def __init__(self, path="", folder_names=[]):
        self.CPV_CODES = [x.code for x in CPVCode.objects.all()]
        self.TED_COUNTRIES = [x.name for x in TedCountry.objects.all()]

        path = path or get_archives_path()
        self.xml_files = [
            os.path.join(path, folder, xml_file)
            for folder in folder_names
            for xml_file in os.listdir(os.path.join(path, folder))
        ]
        self.folders = [os.path.join(path, folder) for folder in folder_names]

    def _parse_notice(self, content, tenders, xml_file, codes, set_notified):
        soup = BeautifulSoup(content, "html.parser")

        if not tenders or self.file_in_tender_list(xml_file, tenders):
            cpv_elements = soup.find_all("cpv_code") or soup.find_all(
                "original_cpv"
            )
            cpv_codes = set([c.get("code") for c in cpv_elements])

            doc_type = soup.find("td_document_type").text
            country = soup.find("iso_country").get("value")
            auth_type = soup.find("aa_authority_type").text

            accept_notice = (
                    cpv_codes & set(self.CPV_CODES)
                    and doc_type in settings.TED_DOC_TYPES
                    and country in self.TED_COUNTRIES
                    and auth_type == settings.TED_AUTH_TYPE
            )

            if not accept_notice:
                self.xml_files.remove(xml_file)
                os.remove(xml_file)
                raise StopIteration
            else:
                codes[xml_file] = cpv_codes
        else:
            self.xml_files.remove(xml_file)
            os.remove(xml_file)
            raise StopIteration

        tender = dict()
        tender["reference"] = soup.find("ted_export").get("doc_id") or ""
        tender["notice_type"] = soup.find("td_document_type").text

        title = soup.find("ml_ti_doc", {"lg": "EN"})
        if title:
            parts = [
                e.text
                for e in title.children
                if isinstance(e, element.Tag)
            ]
            tender["title"] = "{0}-{1}: {2}".format(*parts)
        else:
            tender["title"] = ""

        try:
            tender["organization"] = (
                    soup.find("aa_name", {"lg": "EN"}) or soup.find("aa_name")
            ).text
        except AttributeError:
            tender["organization"] = ""

        try:
            published_str = soup.find("date_pub").text
            tender["published"] = datetime.strptime(published_str, "%Y%m%d").date()
        except (AttributeError, ValueError):
            tender["published"] = ""

        try:
            deadline = soup.find("dt_date_for_submission").text
            tender["deadline"] = make_aware(datetime.strptime(deadline, "%Y%m%d %H:%M"))
        except (AttributeError, ValueError):
            tender["deadline"] = ""

        if tender["deadline"]:
            time_now = datetime.now()
            time_utc = datetime.utcnow()
            add_hours = round(float((time_utc - time_now).total_seconds()) / 3600)
            tender["deadline"] += timedelta(hours=add_hours)

        sections = soup.find("form_section").find_all(lg="EN")
        if sections:
            section = sections[0]
            descriptions = section.findAll("short_descr")[:2]

            try:
                title = "Title:\n\t" + section.find("title").get_text() + "\n\n"
            except AttributeError:
                title = ""

            try:
                estimated_total = (
                        "Estimated total: "
                        + section.find("val_estimated_total").get_text()
                        + " "
                        + str(section.find("val_estimated_total")["currency"])
                        + "\n\n"
                )
            except AttributeError:
                estimated_total = ""

            try:
                lots = (
                        "Tenders may be submitted for maximum number of lots: "
                        + section.find("lot_max_number").get_text()
                        + "\n\n"
                )
            except AttributeError:
                lots = ""

            procurement_desc = ""

            try:
                short_desc = (
                        "Short Description:"
                        + "\n\t"
                        + str(descriptions[0].get_text())
                        + "\n\n"
                )
            except (AttributeError, IndexError):
                short_desc = ""

            try:
                procurement_desc = descriptions[1]
                procurement_desc = (
                        "Description of the procurement:"
                        + "\n\t"
                        + str(descriptions[1].get_text())
                )
            except IndexError:
                pass

            tender["description"] = (
                    title + estimated_total + lots + short_desc + procurement_desc
            )
        else:
            tender["description"] = ""

        url = soup.find("uri_doc")
        try:
            tender["url"] = url.text.replace(url.get("lg"), "EN")
        except AttributeError:
            tender["url"] = ""

        tender["source"] = "TED"

        winners = []
        if tender["notice_type"] == "Contract award notice":
            self.update_winners(winners, soup)

        tender["notified"] = set_notified

        return tender, winners

    @staticmethod
    def file_in_tender_list(xml_file, tenders):
        tender_references = list(map(lambda t: t.reference, tenders))
        return os.path.basename(xml_file).replace("_", "-").replace(".xml", "") in tender_references

    def parse_notices(self, tenders, set_notified):
        changed_tenders = []
        codes = {}
        tenders_count = 0

        # self.xml_files[:] is used instead of self.xml_files because as we are iterating over
        # the list, we"re deleting it"s entries if they doesn't match our criteria
        # changing it would result in a failure of deleting all subsequent files when the iteration ends

        for xml_file in self.xml_files[:]:
            with open(xml_file, "r") as f:
                try:
                    tender, winners = self._parse_notice(f.read(), tenders, xml_file, codes, set_notified)
                except StopIteration:
                    continue

                if winners:
                    for winner in winners:
                        self.save_winner(tender, winner)
                created, attr_changes = self.save_tender(tender, codes.get(xml_file, []))

                if created:
                    tenders_count += 1

                if not created and attr_changes:
                    changed_tenders.append((tender, attr_changes))

            os.remove(xml_file)

        return changed_tenders, tenders_count

    @staticmethod
    def update_winners(winners, soup):
        sections = soup.find("form_section").find_all(lg="EN")
        if sections:
            section = sections[0]
            awarded_contracts = section.find_all("awarded_contract")
            for awarded_contract in awarded_contracts:

                try:
                    date_conclusion_contract = awarded_contract.find("date_conclusion_contract").text
                    award_date = datetime.strptime(date_conclusion_contract, "%Y-%m-%d")
                except (AttributeError, TypeError, ValueError):
                    award_date = date.today()

                try:
                    val_total = awarded_contract.find("val_total")
                    contract_value = float(val_total.text)
                    currency_currency = val_total.get("currency")
                except (AttributeError, TypeError, ValueError):
                    contract_value = 0
                    currency_currency = "N/A"

                contractors = awarded_contract.find_all("contractor")
                for contractor in contractors:
                    winner = {}

                    officialname = contractor.find("officialname")
                    if officialname:
                        winner["vendor"] = officialname.text
                    else:
                        winner["vendor"] = ""

                    winner["award_date"] = award_date
                    winner["value"] = contract_value
                    winner["currency"] = currency_currency

                    winners.append(winner)

    @staticmethod
    def save_winner(tender_fields, winner_fields):
        reference = tender_fields["reference"]
        tender_entry = Tender.objects.filter(reference=reference).first()

        if tender_entry:
            Winner.objects.get_or_create(tender=tender_entry, **winner_fields)

        return

    @staticmethod
    def save_tender(tender, codes):
        old_tender = Tender.objects.filter(reference=tender["reference"]).first()
        new_tender, created = Tender.objects.update_or_create(
            reference=tender["reference"],
            defaults=dict(tender, **{"cpv_codes": ", ".join(codes)}),
        )

        attr_changes = {}
        for attr, value in [(k, v) for (k, v) in tender.items()]:
            old_value = getattr(old_tender, str(attr), None)
            if str(value) != str(old_value):
                attr_changes.update({attr: (old_value, value)})

        return created, attr_changes


def get_archives_path():
    return os.path.join(settings.FILES_DIR, "TED_archives")


def process_daily_archive(given_date):
    w = TEDWorker(given_date)

    message = ""

    while True:
        try:
            w.ftp_download_daily_archives()
            w.parse_notices([], True)
            message = f"Updated {given_date} TED tenders"
            break
        except error_perm as err:
            if err.args[0][:3] == "530":
                time.sleep(30)
                continue
            else:
                raise
        except Exception as e:
            message = str(e)
            break

    return message
