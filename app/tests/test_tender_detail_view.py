from bs4 import BeautifulSoup

from django.urls import reverse
from django.contrib.auth.models import User
from django.test import override_settings

from app.factories import TenderFactory, KeywordFactory,TagsFactory
from app.tests.base import BaseTestCase


class TendersDetailViewTests(BaseTestCase):
    def setUp(self):
        super(TendersDetailViewTests, self).setUp()
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_detail_view_no_tender(self):
        url = reverse('tender_detail_view', kwargs={'pk': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_one_tender(self):
        new_tender = TenderFactory()
        url = reverse('tender_detail_view', kwargs={'pk': new_tender.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_tender.title)
        self.assertContains(response, new_tender.reference)

    def test_detail_view_one_tender_has_keywords(self):
        KeywordFactory(value='python')
        KeywordFactory(value='drupal')
        new_tender = TenderFactory(title='Tender_1 python', description='Tender_1 drupal')
        url = reverse('tender_detail_view', kwargs={'pk': new_tender.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tender_1 <mark>python</mark>')
        self.assertContains(response, 'Tender_1 <mark>drupal</mark>')

        soup = BeautifulSoup(response.content.decode(), 'html.parser')
        response.content = soup.get_text()

        self.assertContains(response, new_tender.title)
        self.assertContains(response, new_tender.reference)

    @override_settings(TENDER_KEYWORDS='')
    def test_detail_view_one_tender_has_keywords_with_no_keywords_set(self):
        new_tender = TenderFactory(title='Tender_2 python', description='Tender_2 drupal')
        url = reverse('tender_detail_view', kwargs={'pk': new_tender.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_tender.title)
        self.assertContains(response, new_tender.reference)
        self.assertContains(response, 'Tender_2 python')
        self.assertContains(response, 'Tender_2 drupal')
    
    def test_detail_view_one_tender_has_tags(self):
        tag1 = TagsFactory()
        tag2 = TagsFactory(name='tag 2')
        new_tender = TenderFactory(title='Tender_3', description='Tender_3 contains tags')
            
        new_tender.tags.add(tag1,tag2)
        new_tender.refresh_from_db()
        tender_tags_values= [tag.name for tag in new_tender.tags.all()]
        
        url = reverse('tender_detail_view', kwargs={'pk': new_tender.id})
        response = self.client.get(url)
        soup = BeautifulSoup(response.content.decode(), 'html.parser')
        response.content = soup.get_text()
        
        self.assertIn(tag1, new_tender.tags.all())
        self.assertIn(tag2,new_tender.tags.all())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ', '.join(tender_tags_values))