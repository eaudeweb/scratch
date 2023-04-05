from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail, management
from django.template.loader import render_to_string
from django.utils import timezone

from app.factories import (
    AwardFactory, TenderFactory, KeywordFactory,
    UNSPCCodeFactory, UserFactory
)
from app.notifications import build_email
from app.models import Tender
from app.tests.base import BaseTestCase
from app.utils import emails_to_notify


class SendMailTest(BaseTestCase):
    def setUp(self):
        super(SendMailTest, self).setUp()
        self.keyword = KeywordFactory()
        self.tender1 = TenderFactory(
            reference='RFQ 47-2019',
            title='test_title1',
            url='https://www.ungm.org/Public/Notice/94909',
            published=datetime.now(timezone.utc) - timedelta(days=2),
            deadline=datetime.now(timezone.utc) +
            timedelta(days=3) - timedelta(hours=1),
        )

        self.tender2 = TenderFactory(
            reference='2019/FLCHI/FLCHI/102665',
            title='test_title2 python',
            url='https://www.ungm.org/Public/Notice/94920',
            published=datetime.now(timezone.utc) - timedelta(days=3),
            deadline=datetime.now(timezone.utc) +
            timedelta(days=7) - timedelta(hours=1),
        )

        self.tender3 = TenderFactory(
            reference='RFP 56956',
            title='test_title3',
            url='https://www.ungm.org/Public/Notice/92850',
            published=datetime.now(timezone.utc) - timedelta(days=1),
            deadline=datetime.now(timezone.utc) +
            timedelta(days=1) - timedelta(hours=1),
        )

        self.user = UserFactory()
        self.tender1.followers.add(self.user)

        UNSPCCodeFactory()

    def test_mailing(self):
        subject = 'New tenders available'
        recipients = emails_to_notify()

        html_content = render_to_string(
            'mails/new_tenders.html',
            {
                'tenders': [self.tender1, self.tender2, self.tender3],
                'domain': settings.BASE_URL,
            },
        )

        email = build_email(subject, recipients, None, html_content)
        email.send()

        self.assertEqual(len(mail.outbox), 1)

        body = mail.outbox[0].body
        alt_body = mail.outbox[0].alternatives[0][0]

        self.assertEqual(self.tender1.title in body, True)
        self.assertEqual(self.tender2.title in body, True)
        self.assertEqual(self.tender3.title in body, True)

        self.assertEqual(self.tender1.organization in alt_body, True)
        self.assertEqual(self.tender2.organization in alt_body, True)
        self.assertEqual(self.tender3.organization in alt_body, True)

    def test_notify_tenders(self):
        management.call_command('notify_tenders')
        self.assertEqual(len(mail.outbox), 3)

        mail1 = mail.outbox[0].alternatives[0][0]
        mail2 = mail.outbox[1].alternatives[0][0]
        mail3 = mail.outbox[2].alternatives[0][0]

        self.assertEqual(self.tender3.title in mail1, True)
        self.assertEqual(self.tender1.title in mail2, True)
        self.assertEqual(self.tender2.title in mail3, True)

    def test_notify_tenders_digest(self):
        AwardFactory(tender=self.tender1)

        management.call_command('notify_tenders', digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, 'html.parser')

        tender_list = soup.find('ol', {'class': 'tender-list'}).find_all('a')

        tender_1_url = f"{settings.BASE_URL}/tenders/{self.tender1.id}"
        tender_2_url = f"{settings.BASE_URL}/tenders/{self.tender2.id}"
        tender_3_url = f"{settings.BASE_URL}/tenders/{self.tender3.id}"

        # The tenders in the email are ordered by -published

        self.assertEqual(len(tender_list), 2)
        self.assertEqual(tender_list[0]['href'], tender_3_url)
        self.assertEqual(tender_list[1]['href'], tender_2_url)

        self.assertNotIn(tender_1_url, tender_list)

    def test_notify_awards(self):
        award1 = AwardFactory()
        award2 = AwardFactory()
        award3 = AwardFactory()
        management.call_command('notify_awards')
        self.assertEqual(len(mail.outbox), 3)

        mail1 = mail.outbox[0].alternatives[0][0]
        mail2 = mail.outbox[1].alternatives[0][0]
        mail3 = mail.outbox[2].alternatives[0][0]

        self.assertEqual(award1.tender.title in mail1, True)
        self.assertEqual(award2.tender.title in mail2, True)
        self.assertEqual(award3.tender.title in mail3, True)

    def test_notify_awards_digest(self):
        award1 = AwardFactory()
        award2 = AwardFactory()
        award3 = AwardFactory()
        management.call_command('notify_awards', digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, 'html.parser')

        award_list = soup.find('ol', {'class': 'award-list'}).find_all('a')

        award_tender_url1 = f"{settings.BASE_URL}/awards/{award1.id}"
        award_tender_url2 = f"{settings.BASE_URL}/awards/{award2.id}"
        award_tender_url3 = f"{settings.BASE_URL}/awards/{award3.id}"

        self.assertEqual(len(award_list), 3)
        self.assertEqual(award_list[0]['href'], award_tender_url1)
        self.assertEqual(award_list[1]['href'], award_tender_url2)
        self.assertEqual(award_list[2]['href'], award_tender_url3)

    @patch('app.server_requests.requests')
    def test_mailing_favorites(self, mock_requests):

        with open('app/tests/parser_files/94909.html', 'r') as f:
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.content = f.read()


        with open('app/tests/parser_files/94920.html', 'r') as f:
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.content = f.read()

        with open('app/tests/parser_files/92850.html', 'r') as f:
            mock_response3 = MagicMock()
            mock_response3.status_code = 200
            mock_response3.content = f.read()

        mock_requests.get.side_effect = [mock_response1, ]

        original_tender1_organization = self.tender1.organization
        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 1)

        mock_requests.get.side_effect = [mock_response1, ]

        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender1.organization = 'CHANGE1'
        self.tender1.save()

        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 2)

        mock_requests.get.side_effect = [mock_response1, ]

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.organization = 'CHANGE2'
        self.tender3.save()

        management.call_command('notify_favorites')
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.assertEqual('Favorite tender(s) update' in message, True)
        self.assertEqual(original_tender1_organization in message, False)
        self.assertEqual(self.tender1.organization in message, True)
        self.assertEqual(self.tender3.organization in message, False)

    @patch('app.server_requests.requests')
    def test_mailing_favorites_digest(self, mock_requests):

        with open('app/tests/parser_files/94909.html', 'r') as f:
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.content = f.read()


        with open('app/tests/parser_files/94920.html', 'r') as f:
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.content = f.read()

        with open('app/tests/parser_files/92850.html', 'r') as f:
            mock_response3 = MagicMock()
            mock_response3.status_code = 200
            mock_response3.content = f.read()

        mock_requests.get.side_effect = [mock_response3, mock_response1, mock_response2 ]

        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.organization = 'CHANGE2'
        self.tender2.followers.add(self.user)
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.organization = 'CHANGE3'
        self.tender3.followers.add(self.user)
        self.tender3.save()

        management.call_command('notify_favorites', digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, 'html.parser')

        tender_list = soup.find('ol', {'class': 'tender-list'}).find_all('a')
        self.assertEqual(len(tender_list), 3)

        tender_1_url = f"{settings.BASE_URL}/tenders/{self.tender1.id}"
        tender_2_url = f"{settings.BASE_URL}/tenders/{self.tender2.id}"
        tender_3_url = f"{settings.BASE_URL}/tenders/{self.tender3.id}"

        # The tenders in the email are ordered by -published
        self.assertEqual(tender_list[0]['href'], tender_3_url)
        self.assertEqual(tender_list[1]['href'], tender_1_url)
        self.assertEqual(tender_list[2]['href'], tender_2_url)

    @patch('app.server_requests.requests')
    def test_mailing_keywords(self, mock_requests):

        with open('app/tests/parser_files/94909.html', 'r') as f:
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.content = f.read()


        with open('app/tests/parser_files/94920.html', 'r') as f:
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.content = f.read()

        with open('app/tests/parser_files/92850.html', 'r') as f:
            mock_response3 = MagicMock()
            mock_response3.status_code = 200
            mock_response3.content = f.read()

        mock_requests.get.side_effect = [mock_response3, mock_response1, mock_response2]

        management.call_command('notify_keywords')
        self.assertEqual(len(mail.outbox), 1)

        mock_requests.get.side_effect = [mock_response1, mock_response2]

        self.tender2.organization = 'CHANGE1'
        self.tender2.save()

        management.call_command('notify_keywords')
        self.assertEqual(len(mail.outbox), 2)

        mock_requests.get.side_effect = [mock_response1, mock_response2]

        self.tender3.organization = 'CHANGE2'
        self.tender3.save()

        management.call_command('notify_keywords')
        self.assertEqual(len(mail.outbox), 2)

        message = mail.outbox[0].alternatives[0][0]
        self.assertEqual('Keyword tender(s) update' in message, True)
        self.assertEqual(self.tender2.organization in message, False)
        self.assertEqual(self.tender3.organization in message, False)

    @patch('app.server_requests.requests')
    def test_mailing_keywords_digest(self, mock_requests):

        with open('app/tests/parser_files/94909.html', 'r') as f:
            mock_response1 = MagicMock()
            mock_response1.status_code = 200
            mock_response1.content = f.read()


        with open('app/tests/parser_files/94920.html', 'r') as f:
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.content = f.read()

        with open('app/tests/parser_files/92850.html', 'r') as f:
            mock_response3 = MagicMock()
            mock_response3.status_code = 200
            mock_response3.content = f.read()

        mock_requests.get.side_effect = [mock_response3, mock_response1, mock_response2]

        self.tender1 = Tender.objects.get(reference=self.tender1.reference)
        self.tender1.title = 'test_title1 python'
        self.tender1.save()

        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.title = 'test_title2 changed python'
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.title = 'test_title3 python'
        self.tender3.save()

        management.call_command('notify_keywords', digest=True)
        self.assertEqual(len(mail.outbox), 1)

        alt_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(alt_body, 'html.parser')

        tender_list = soup.find('ol', {'class': 'tender-list'}).find_all('a')
        self.assertEqual(len(tender_list), 3)
        email_urls = {t['href'] for t in tender_list}
        tender_1_url = f"{settings.BASE_URL}/tenders/{self.tender1.id}"
        tender_2_url = f"{settings.BASE_URL}/tenders/{self.tender2.id}"
        tender_3_url = f"{settings.BASE_URL}/tenders/{self.tender3.id}"

        db_urls = {tender_1_url, tender_2_url, tender_3_url}
        self.assertEqual(email_urls, db_urls)

    def test_deadline_notification(self):
        self.tender2 = Tender.objects.get(reference=self.tender2.reference)
        self.tender2.followers.add(self.user)
        self.tender2.save()

        self.tender3 = Tender.objects.get(reference=self.tender3.reference)
        self.tender3.followers.add(self.user)
        self.tender3.save()

        management.call_command('deadline_notifications')
        self.assertEqual(len(mail.outbox), 3)

        mail1 = mail.outbox[0].alternatives[0][0]
        mail2 = mail.outbox[1].alternatives[0][0]
        mail3 = mail.outbox[2].alternatives[0][0]

        tender_1_url = f"{settings.BASE_URL}/tenders/{self.tender1.id}"
        tender_2_url = f"{settings.BASE_URL}/tenders/{self.tender2.id}"
        tender_3_url = f"{settings.BASE_URL}/tenders/{self.tender3.id}"

        # The tenders in the email are ordered by -published
        self.assertEqual(tender_3_url in mail1, True)
        self.assertEqual(tender_1_url in mail2, True)
        self.assertEqual(tender_2_url in mail3, True)

    def test_notify_renewal(self):

        months = 4

        three_months_from_now = timezone.now().date() + relativedelta(months=3)
        five_months_from_now = timezone.now().date() + relativedelta(months=5)

        award1 = AwardFactory(renewal_date=three_months_from_now)
        award2 = AwardFactory(renewal_date=three_months_from_now)
        award3 = AwardFactory(renewal_date=five_months_from_now)

        self.assertEqual(award1.renewal_notified, False)
        self.assertEqual(award2.renewal_notified, False)
        self.assertEqual(award3.renewal_notified, False)

        management.call_command('notify_renewal', months=months)
        self.assertEqual(len(mail.outbox), 1)

        award1.refresh_from_db()
        award2.refresh_from_db()
        award3.refresh_from_db()

        email_body = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(email_body, 'html.parser')

        award_list = soup.find('ol', {'class': 'award-list'}).find_all('a')
        self.assertEqual(len(award_list), 2)
        self.assertEqual(award_list[0]['href'], award1.tender.url)
        self.assertEqual(award_list[1]['href'], award2.tender.url)

        self.assertEqual(award1.renewal_notified, True)
        self.assertEqual(award2.renewal_notified, True)
        self.assertEqual(award3.renewal_notified, False)
