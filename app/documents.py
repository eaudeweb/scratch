from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import normalizer, tokenizer

from .models import Tender, Winner

case_insensitive_analyzer = analyzer(
    'case_insensitive_analyzer',
    tokenizer="standard",
    token_chars=["whitespace", "punctuation"],
    filter=['lowercase']
)

case_insensitive_normalizer = normalizer(
    type="custom",
    name_or_instance='case_insensitive_normalizer',
    char_filter=[],
    filter="lowercase",
)

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
class TenderDoc(DocType):
    description = fields.TextField(
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}
    )

    title = fields.TextField(
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}
    )

    class Meta:
        model = Tender
        fields = [
            'reference',
            'unspsc_codes',
            'cpv_codes',
            'organization',
            'source',
            'notified',
        ]


@winner.doc_type
class WinnerDoc(DocType):
    tender_title = fields.KeywordField(attr='tender.title')
    vendor_name = fields.KeywordField(attr='vendor.name')
    value = fields.TextField(attr="convert_value_to_string")

    class Meta:
        model = Winner
        fields = [
            'currency',
        ]
