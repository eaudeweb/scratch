from django.test import TestCase
from app.factories import TenderFactory,TagsFactory
from django.urls import reverse



class TenderTagViewTestCase(TestCase):
  
    def test_add_tag(self):
        
        tender = TenderFactory(title='test_title_1')
        tag = TagsFactory()

        response = self.client.post(
            reverse('tender_tag_view', kwargs={'pk': tender.pk}),
            {'tag_name': tag.name}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(tag, tender.tags.all())
    