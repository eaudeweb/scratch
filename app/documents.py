from django_elasticsearch_dsl import  DocType, Index
from .models import Tender, Winner, UNSPSCCode, CPVCode

tender = Index('tenders')
tender.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@tender.doc_type
class WinnerDocument(DocType):
    class Meta:
        model = Tender
        fields = [
            'title',
        ]
