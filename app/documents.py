from django_elasticsearch_dsl import  DocType, Index, fields
from .models import Tender, Winner, UNSPSCCode, CPVCode

tender = Index('tenders')
tender.settings(
    number_of_shards=1,
    number_of_replicas=0
)

winner = Index('winners')
winner.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@tender.doc_type
class TenderDocument(DocType):
    class Meta:
        model = Tender
        fields = [
            'title',
            'reference',
            'description',
            'unspsc_codes',
            'cpv_codes',
            'organization',
            'source',
        ]


@winner.doc_type
class WinnerDocument(DocType):
    tender_title = fields.KeywordField(attr='tender.title')

    class Meta:
        model = Winner
        fields = [
            'vendor',
            'value',
            'currency',
        ]
