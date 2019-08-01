from django.core.management.base import BaseCommand
from ftplib import FTP
from bs4 import BeautifulSoup, element
from app.models import Tender, TenderDocument, Winner, WorkerLog, set_notified, last_update
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .ted_data import *
import tarfile
import os


class Command(BaseCommand):

    def handle(self, *args, **options):
        w = TEDWorker()
        w.ftp_download()
        w.parse_notices()


class TEDWorker:
    def __init__(self, archives=[]):
        self.path = get_archives_path()
        self.archives = archives

    def ftp_download(self):
        ftp = FTP(settings.FTP_URL)
        ftp.login(user='guest', passwd='guest')

        last_date = last_update('TED') or \
            days_ago(settings.TED_DAYS_AGO)
        last_month = last_date.strftime('%m')
        last_year = last_date.strftime('%Y')

        ftp.cwd(f'daily-packages/{last_year}/{last_month}')

        archives = ftp.nlst()
        today = date.today()

        while last_date < today:
            archive_name = get_archive_name(last_date, archives)
            if archive_name:
                if not os.path.exists(self.path):
                    os.makedirs(self.path)
                file_path = os.path.join(self.path, archive_name)
                with open(file_path, 'wb') as f:
                    ftp.retrbinary('RETR %s' % archive_name,
                                   lambda data: f.write(data))
                self.archives.append(file_path)
            add_worker_log('TED', last_date)

            last_date += timedelta(1)

            if last_year != last_date.strftime('%Y'):
                last_year = last_date.strftime('%Y')
                last_month = last_date.strftime('%m')
                ftp.cwd('../../{}/{}'.format(last_year, last_month))
                archives = ftp.nlst()
            elif last_month != last_date.strftime('%m'):
                last_month = last_date.strftime('%m')
                ftp.cwd('../{}'.format(last_month))
                archives = ftp.nlst()

        ftp.quit()

    def parse_notices(self):
        for archive_path in self.archives:
            folder_name = extract_data(archive_path, self.path)
            p = TEDParser(self.path, [folder_name])
            p.parse_notices()


class TEDParser(object):

    def __init__(self, path='', folder_names=[]):
        path = path or get_archives_path()
        self.xml_files = [
            os.path.join(path, folder, xml_file)
            for folder in folder_names
            for xml_file in os.listdir(os.path.join(path, folder))
        ]
        self.folders = [os.path.join(path, folder) for folder in folder_names]

    @staticmethod
    def _parse_notice(content):
        soup = BeautifulSoup(content, 'html.parser')

        tender = dict()
        tender['reference'] = soup.find('ted_export').get('doc_id')
        tender['notice_type'] = soup.find('td_document_type').text
        parts = [e.text for e in soup.find('ml_ti_doc', {'lg': 'EN'}).children
                 if isinstance(e, element.Tag)]
        tender['title'] = u'{0}-{1}: {2}'.format(*parts)
        tender['organization'] = (soup.find('aa_name', {'lg': 'EN'}) or
                                  soup.find('aa_name')).text
        published_str = soup.find('date_pub').text
        tender['published'] = datetime.strptime(published_str, '%Y%m%d').date()

        deadline = soup.find('dt_date_for_submission')
        if deadline:
            try:
                deadline = datetime.strptime(deadline.text, '%Y%m%d %H:%M')
            except ValueError:
                deadline = datetime.strptime(deadline.text, '%Y%m%d')
        tender['deadline'] = deadline

        section = soup.find('contract', {'lg': 'EN'})
        desc = section.find('short_contract_description') if section else None
        tender['description'] = ''.join([str(e) for e in desc.contents]) \
            if desc else ''

        try:
            tender['description'] = tender['description'].decode('utf-8')
        except AttributeError:
            pass

        url = soup.find('uri_doc')
        tender['url'] = url.text.replace(url.get('lg'), 'EN')
        tender['source'] = 'TED'

        winner = {}
        if tender['notice_type'] == 'Contract award':
            update_winner(winner, soup)

        return tender, winner

    def parse_notices(self):
        self._filter_notices()
        for xml_file in self.xml_files:
            with open(xml_file, 'r') as f:
                tender, winner = self._parse_notice(f.read())
                if winner:
                    save_winner(tender, winner)
                else:
                    save_tender(tender)
            os.remove(xml_file)

    def _filter_notices(self):
        for xml_file in self.xml_files[:]:
            with open(xml_file, 'r') as f:

                soup = BeautifulSoup(f.read(), 'html.parser')

                cpv_elements = soup.find_all('cpv_code') \
                    or soup.find_all('original_cpv')
                cpv_codes = set([c.get('code') for c in cpv_elements])

                doc_type = soup.find('td_document_type').text
                country = soup.find('iso_country').get('value')
                auth_type = soup.find('aa_authority_type').text

                accept_notice = (
                    cpv_codes & set(CPV_CODES) and
                    doc_type in TED_DOC_TYPES and
                    country in TED_COUNTRIES and
                    auth_type == TED_AUTH_TYPE
                )

                if not accept_notice:
                    self.xml_files.remove(xml_file)
                    os.remove(xml_file)


def save_tender(tender):
    old_tender = Tender.objects.filter(reference=tender['reference']).first()
    if old_tender:
        for attr, value in [(k, v) for (k, v) in tender.items()
                            if k != 'documents']:

            if attr == 'deadline':
                value = timezone.utc.localize(value)

            setattr(old_tender, attr, value)

        old_tender.save()
        return old_tender

    documents = tender.pop('documents', [])
    tender_entry = Tender(**tender)
    tender_entry.deadline = timezone.utc.localize(tender_entry.deadline)
    tender_entry.save()
    for document in documents:
        save_document_to_models(tender_entry, document)
    tender['documents'] = documents

    return tender_entry


def save_winner(tender_fields, winner_fields):
    reference = tender_fields['reference']
    tender = Tender.objects.filter(reference=reference).first()
    if not tender:
        tender_entry = Tender(**tender_fields)
        tender_entry.deadline = timezone.utc.localize(tender_entry.deadline)
        set_notified(tender_entry)
        tender_entry.save()
    else:
        tender_entry = tender

    winner_entry = Winner(tender=tender_entry, **winner_fields)
    winner_entry.save()

    return tender_entry


def update_winner(winner, soup):
    award_date = soup.find('contract_award_date')
    if award_date:
        fields = {c.name: int(c.text) for c in award_date.contents}
        winner['award_date'] = date(**fields)
    vendor = soup.find('economic_operator_name_address') or \
        soup.find('contact_data_without_responsible_name_chp')
    if vendor:
        winner['vendor'] = vendor.officialname.text \
            if vendor.officialname else None
    value = soup.find('value_cost')
    if value:
        winner['value'] = value.get('fmtval')
        winner['currency'] = value.parent.get('currency')


def save_document_to_models(tender, document):
    document_entry = TenderDocument(tender=tender, **document)
    document_entry.save()


def get_archives_path():
    return os.path.join(settings.FILES_DIR, 'TED_archives')


def days_ago(days):
    return date.today() - timedelta(days=days)


def get_archive_name(last_date, archives):
    starting_name = last_date.strftime('%Y%m%d')
    for archive_name in archives:
        if archive_name.startswith(starting_name):
            return archive_name
    return None


def add_worker_log(source, new_date=None):
    log = WorkerLog(source=source, update=new_date or date.today())
    log.save()


def parse_notices(self):
    for archive_path in self.archives:
        folder_name = self.extract_data(archive_path, self.path)
        p = TEDParser(self.path, [folder_name])
        p.parse_notices()


def extract_data(archive_path, extract_path):
    tf = tarfile.open(archive_path, 'r:gz')
    tf.extractall(extract_path)
    return tf.getnames()[0]
