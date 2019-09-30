import factory

from django.test import TestCase
from django.db.models import signals

class BaseTestCase(TestCase):
    
    def setUp(self):
        signals.post_save.disconnect(sender='app.Keyword', dispatch_uid="keyword_save")
        signals.post_delete.disconnect(sender='app.Keyword', dispatch_uid="keyword_delete")
