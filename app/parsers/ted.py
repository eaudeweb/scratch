import logging
import tarfile
import os
import time

from typing import List, Tuple
from bs4 import BeautifulSoup, element
from datetime import date, datetime, timedelta
from django.conf import settings
from ftplib import error_perm, FTP

from django.utils.timezone import make_aware

from app.models import WorkerLog, Tender, Award, CPVCode, TedCountry, Vendor

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s')


def quit_or_close(ftp):
    try:
        ftp.quit()
    except EOFError:
        ftp.close()


class TEDWorker:
    archives = []

    def __init__(self, last_ted_update=None):
        self.path = get_archives_path()
        if not last_ted_update:
            last_ted_update = date.today()
        self.last_ted_update = last_ted_update

    def ftp_download_tender_archive(self, tenders):
        ftp = self.ftp_login()
        tender_count = tenders.count()
        downloaded = 0
        for tender in tenders:
            ftp_path = tender.published.strftime('%Y/%m')
            ftp.cwd(f'/daily-packages/{ftp_path}')
            archives = ftp.nlst()
            try:
                self.download_archive(ftp, tender.published, archives)
                downloaded += 1
                logging.warning(
                    f"Downloaded {downloaded} out of "
                    f"{tender_count} tender archives."
                )
            except Exception as e:
                logging.error(e, exc_info=True)

        quit_or_close(ftp)

    def ftp_download_latest_archives(self):
        """
        Download latest tender archives and save them in a local directory.
        """
        ftp = self.ftp_login()

        today = date.today()
        last_date = self.last_ted_update or self.last_update('TED')

        while last_date <= today:

            last_month = last_date.strftime('%m')
            last_year = last_date.strftime('%Y')

            try:
                ftp.cwd(f'/daily-packages/{last_year}/{last_month}')
                archives = ftp.nlst()
                self.download_archive(ftp, last_date, archives)
            except error_perm as e:
                # Directory doesn't exist
                logging.warning(e)
                pass

            last_date += timedelta(1)

        quit_or_close(ftp)

    def ftp_download_daily_archives(self):
        last_month = self.last_ted_update.strftime('%m')
        last_year = self.last_ted_update.strftime('%Y')

        ftp = self.ftp_login()
        ftp.cwd(f'/daily-packages/{last_year}/{last_month}')

        archives = ftp.nlst()

        self.download_archive(ftp, self.last_ted_update, archives)

        quit_or_close(ftp)

    def download_archive(self, ftp, archive_date, archives):
        archive_name = self.get_archive_name(archive_date, archives)
        if archive_name:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            file_path = os.path.join(self.path, archive_name)
            with open(file_path, "wb") as f:
                ftp.retrbinary("RETR %s" % archive_name, f.write)
            self.archives.append(file_path)

    def parse_notices(
        self, tenders=None, set_notified=False
    ) -> Tuple[Tuple[dict, dict], int]:
        """
        Parse an archive file, extract all tender data from it and use it to
        update existing tenders or create new ones.
        """
        if tenders is None:
            tenders = []
        all_updated_tenders = []
        folders = []
        total_created_tenders = 0
        for archive_path in self.archives:
            folder_name = self.extract_data(archive_path, self.path)
            if folder_name:
                folders.append(folder_name)
                p = TEDParser(self.path, [folder_name])
                updated_tenders, num_created_tenders = p.parse_notices(
                    tenders, set_notified)
                all_updated_tenders += updated_tenders
                total_created_tenders += num_created_tenders
                folder_date = folder_name[:8]
                formatted_date = datetime.strptime(
                    folder_date, '%Y%m%d').strftime('%d/%m/%Y')
                logging.warning(f'Date {formatted_date} parsed successfully')

        for archive_path in self.archives:
            try:
                os.remove(archive_path)
            except OSError as e:
                logging.warning(e)
                pass

        for folder in folders:
            try:
                os.rmdir(os.path.join(self.path, folder))
            except OSError as e:
                logging.warning(e)
                pass

        return all_updated_tenders, total_created_tenders

    @staticmethod
    def extract_data(archive_path, extract_path):
        try:
            tf = tarfile.open(archive_path, 'r:gz')
            tf.extractall(extract_path)
            return tf.getnames()[0]
        except (EOFError, FileNotFoundError) as e:
            logging.warning(e)

        return

    @staticmethod
    def ftp_login():
        while True:
            try:
                ftp = FTP(settings.TED_FTP_URL)
                ftp.login(
                    user=settings.TED_FTP_USER,
                    passwd=settings.TED_FTP_PASSWORD
                )
                logging.warning("Logged into FTP.")
                return ftp
            except error_perm as e:
                logging.warning(
                    f"Cannot login to FTP, waiting 30 seconds: {e}")
                time.sleep(30)
                logging.warning("Retrying")
                continue

    @staticmethod
    def get_archive_name(last_date, archives):
        starting_name = last_date.strftime('%Y%m%d')
        for archive_name in archives:
            if archive_name.startswith(starting_name):
                return archive_name
        return None

    @staticmethod
    def add_worker_log(source, tenders_count):
        log = WorkerLog(
            source=source, update=date.today(), tenders_count=tenders_count)
        log.save()

    @staticmethod
    def last_update(source):
        worker_log = (
            WorkerLog.objects.filter(source=source).order_by("-update").first()
        )
        return worker_log.update if worker_log else None


class TEDParser(object):
    def __init__(self, path='', folder_names=[]):
        self.CPV_CODES = [x.code for x in CPVCode.objects.all()]
        self.TED_COUNTRIES = [x.name for x in TedCountry.objects.all()]

        path = path or get_archives_path()
        self.xml_files = [
            os.path.join(path, folder, xml_file)
            for folder in folder_names
            for xml_file in os.listdir(os.path.join(path, folder))
        ]
        self.folders = [os.path.join(path, folder) for folder in folder_names]

    def _parse_notice(
        self, content, tenders_to_update, xml_file, codes, set_notified
    ) -> Tuple[dict, List[dict]]:
        """
        :param tenders_to_update: a list of tenders to be updated. If the list
            is empty, we update all tenders and create new ones when the tender
            reference in the file does not correspond to any tender in the
            database.
        """
        if tenders_to_update and not self.file_in_tender_list(
                xml_file, tenders_to_update):
            # Update mode: we only care about updating the tenders on the list,
            # new tenders will not be created. Therefore, if the tender this
            # file is about is not in the list, the file is irrelevant.
            try:
                self.xml_files.remove(xml_file)
                os.remove(xml_file)
            except ValueError:
                pass
            raise StopIteration

        soup = BeautifulSoup(content, 'html.parser')

        cpv_elements = soup.find_all('cpv_code') or soup.find_all(
            'original_cpv'
        )
        cpv_codes = set([c.get('code') for c in cpv_elements])

        doc_type = soup.find('td_document_type').text
        country = soup.find('iso_country').get('value')
        auth_type = soup.find('aa_authority_type').text

        accept_notice = (
            cpv_codes & set(self.CPV_CODES) and (
                doc_type in settings.TED_DOC_TYPES
            ) and country in self.TED_COUNTRIES and (
                auth_type == settings.TED_AUTH_TYPE
            )
        )

        if not accept_notice:
            try:
                self.xml_files.remove(xml_file)
                os.remove(xml_file)
            except ValueError:
                pass
            raise StopIteration
        else:
            codes[xml_file] = cpv_codes

        tender = dict()
        tender['reference'] = soup.find('ted_export').get('doc_id') or ''
        tender['notice_type'] = soup.find('td_document_type').text

        title = soup.find('ml_ti_doc', {'lg': 'EN'})
        if title:
            parts = [
                e.text
                for e in title.children
                if isinstance(e, element.Tag)
            ]
            tender['title'] = '{0}-{1}: {2}'.format(*parts)
            tender['title'] = tender['title'][:255]
        else:
            tender['title'] = ''

        try:
            tender['organization'] = (
                soup.find('aa_name', {'lg': 'EN'}) or soup.find('aa_name')
            ).text
        except AttributeError:
            tender['organization'] = ''

        try:
            published_str = soup.find('date_pub').text
            tender['published'] = datetime.strptime(
                published_str, '%Y%m%d').date()
        except (AttributeError, ValueError):
            tender['published'] = None

        try:
            deadline = soup.find('dt_date_for_submission').text
            tender['deadline'] = make_aware(
                datetime.strptime(deadline, '%Y%m%d %H:%M'))
        except (AttributeError, ValueError):
            tender['deadline'] = None

        if tender['deadline']:
            time_now = datetime.now()
            time_utc = datetime.utcnow()
            add_hours = round(
                float((time_utc - time_now).total_seconds()) / 3600)
            tender['deadline'] += timedelta(hours=add_hours)

        sections = soup.find('form_section').find_all(lg='EN')
        if sections:
            section = sections[0]
            descriptions = section.findAll('short_descr')[:2]

            try:
                title = 'Title:\n\t' + section.find('title').get_text() + '\n\n'
            except AttributeError:
                title = ''

            try:
                estimated_total = (
                    'Estimated total: '
                    + section.find('val_estimated_total').get_text()
                    + ' '
                    + str(section.find('val_estimated_total')['currency'])
                    + '\n\n'
                )
            except AttributeError:
                estimated_total = ''

            try:
                lots = (
                    'Tenders may be submitted for maximum number of lots: '
                    + section.find('lot_max_number').get_text()
                    + '\n\n'
                )
            except AttributeError:
                lots = ''

            procurement_desc = ''

            try:
                short_desc = (
                    'Short Description:'
                    + '\n\t'
                    + str(descriptions[0].get_text())
                    + '\n\n'
                )
            except (AttributeError, IndexError):
                short_desc = ''

            try:
                procurement_desc = descriptions[1]
                procurement_desc = 'Description of the procurement:' + (
                    '\n\t' + str(descriptions[1].get_text())
                )
            except IndexError:
                pass

            tender['description'] = (
                title + estimated_total + lots + short_desc + procurement_desc
            )
        else:
            tender['description'] = ''

        url = soup.find('uri_doc')
        try:
            tender['url'] = url.text.replace(url.get('lg'), 'EN')
        except AttributeError:
            tender['url'] = ''

        tender['source'] = 'TED'

        awards = []
        if tender['notice_type'] == 'Contract award':
            self.update_contract_award_awards(awards, soup, set_notified)

        if tender['notice_type'] == 'Contract award notice':
            self.update_contract_award_notice_awards(awards, soup, set_notified)

        return tender, awards

    @staticmethod
    def file_in_tender_list(xml_file, tenders):
        tender_references = [t.reference for t in tenders]
        return os.path.basename(xml_file).replace(
            '_', '-').replace('.xml', '') in tender_references

    def parse_notices(
        self, tenders: List[dict], set_notified: bool
    ) -> Tuple[List[Tuple[dict, dict]], int]:
        changed_tenders = []
        codes = {}
        num_created_tenders = 0

        # self.xml_files[:] is used instead of self.xml_files because as we are
        # iterating over the list, we"re deleting it"s entries if they doesn't
        # match our criteria changing it would result in a failure of deleting
        # all subsequent files when the iteration ends

        for xml_file in self.xml_files[:]:
            with open(xml_file, 'r') as f:
                try:
                    tender_dict, awards = self._parse_notice(
                        f.read(), tenders, xml_file, codes, set_notified)
                except StopIteration:
                    continue

                created, attr_changes = self.save_tender(
                    tender_dict, codes.get(xml_file, []))

                if awards:
                    for award_dict in awards:
                        self.save_award(tender_dict, award_dict)

                if created:
                    num_created_tenders += 1

                if not created and attr_changes:
                    changed_tenders.append((tender_dict, attr_changes))

            os.remove(xml_file)

        # Only the changed tender info is returned, the created ones are not
        return changed_tenders, num_created_tenders

    @staticmethod
    def update_contract_award_awards(awards, soup, set_notified):
        """
        Extract data from the soup and populate a dictionary representing an
        award, subsequently adding it to the list of awards received as
        parameter.
        """
        award = {}
        award_date = soup.find('contract_award_date')
        if award_date:
            fields = {}
            for c in award_date.contents:
                try:
                    fields[c.name] = int(c.text)
                except AttributeError:
                    pass
            award['award_date'] = date(**fields)
        vendor = soup.find('economic_operator_name_address') or soup.find(
            'contact_data_without_responsible_name_chp'
        )
        if vendor:
            award['vendor'] = (
                vendor.officialname.text if vendor.officialname else None
            )
        value = soup.find('value_cost')
        if value:
            award['value'] = value.get('fmtval')
            award['currency'] = value.parent.get('currency')

        award['notified'] = set_notified

        awards.append(award)

    @staticmethod
    def update_contract_award_notice_awards(awards, soup, set_notified):
        sections = soup.find('form_section').find_all(lg='EN')
        if sections:
            section = sections[0]
            awarded_contracts = section.find_all('awarded_contract')
            for awarded_contract in awarded_contracts:

                try:
                    date_conclusion_contract = awarded_contract.find(
                        'date_conclusion_contract').text
                    award_date = datetime.strptime(
                        date_conclusion_contract, '%Y-%m-%d')
                except (AttributeError, TypeError, ValueError):
                    award_date = date.today()

                try:
                    val_total = awarded_contract.find('val_total')
                    contract_value = float(val_total.text)
                    currency_currency = val_total.get('currency')
                except (AttributeError, TypeError, ValueError):
                    contract_value = 0
                    currency_currency = 'N/A'

                contractors = awarded_contract.find_all('contractor')
                if contractors:
                    award = {
                        "vendors": [],
                        "award_date": award_date,
                        "value": contract_value,
                        "currency": currency_currency,
                        "notified": set_notified,

                    }
                    for contractor in contractors:
                        officialname = contractor.find('officialname')
                        if officialname:
                            award['vendors'].append(officialname.text)

                    awards.append(award)

    @staticmethod
    def save_award(tender_dict, award_dict) -> Award:
        reference = tender_dict['reference']
        tender_entry = Tender.objects.filter(reference=reference).first()

        if tender_entry:
            vendors = award_dict.pop('vendors')
            vendor_objects = []
            for vendor in vendors:
                vendor_object, _ = Vendor.objects.get_or_create(name=vendor)
                vendor_objects.append(vendor_object)
            award, created = Award.objects.get_or_create(
                tender=tender_entry, defaults=award_dict)
            if not created:
                award.value += award_dict['value']
                award.save()
            award.vendors.add(*vendor_objects)
            return award

    @staticmethod
    def save_tender(tender_dict, codes) -> Tuple[bool, dict]:
        old_tender = Tender.objects.filter(
            reference=tender_dict['reference']).first()
        new_tender, created = Tender.objects.update_or_create(
            reference=tender_dict['reference'],
            defaults=dict(tender_dict, **{'cpv_codes': ', '.join(codes)}),
        )

        attr_changes = {}
        for attr, value in [(k, v) for (k, v) in tender_dict.items()]:
            old_value = getattr(old_tender, str(attr), None)
            if str(value) != str(old_value):
                attr_changes.update({attr: (old_value, value)})
        return created, attr_changes


def get_archives_path():
    return os.path.join(settings.FILES_DIR, 'TED_archives')


def process_daily_archive(given_date):
    w = TEDWorker(given_date)
    w.ftp_download_daily_archives()
    w.parse_notices([], True)
    return f"Updated {given_date} TED tenders"
