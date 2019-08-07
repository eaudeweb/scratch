from django.test import TestCase
from app.models import Tender
from django.contrib.auth.models import User


def create_tender(status):
    return Tender.objects.create(
        title='Tender3',
        reference='RFC/TEST/1237',
        url='http://test.com',
        source='UNGM',
        unspsc_codes='98765',
        favourite=True,
    )


def get_url(tender_id):
    return '/app/tenders/delete/' + str(tender_id) + '/'


class TendersFavouriteTests(TestCase):
    def setUp(self):
        user = User.objects.create(username='test_user')
        user.set_password('12345')
        user.save()
        logged_in = self.client.login(username='test_user', password='12345')
        self.assertEqual(logged_in, True)

    def test_delete_tender(self):
        new_delete_tender = create_tender(True)
        url = get_url(new_delete_tender.id)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        tender_deleted = Tender.objects.filter(reference='RFC/TEST/1237')
        self.assertQuerysetEqual(tender_deleted, [])