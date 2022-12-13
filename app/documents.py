from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import normalizer

from .models import Tender, Award, TenderDocument

case_insensitive_analyzer = analyzer(
    'case_insensitive_analyzer',
    tokenizer='standard',
    token_chars=['whitespace', 'punctuation'],
    filter=['lowercase']
)

case_insensitive_normalizer = normalizer(
    type='custom',
    name_or_instance='case_insensitive_normalizer',
    char_filter=[],
    filter='lowercase',
)

tender = Index('tenders')
tender.settings(
    number_of_shards=1,
    number_of_replicas=0,
)

award = Index('awards')
award.settings(
    number_of_shards=1,
    number_of_replicas=0,
)

tender_document = Index('tender_documents')
tender_document.settings(
    number_of_shards=1,
    number_of_replicas=0,
)


@tender.doc_type
class TenderDoc(Document):
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

    reference = fields.KeywordField(attr='reference')

    class Django:
        model = Tender
        fields = [
            'unspsc_codes',
            'cpv_codes',
            'organization',
            'source',
            'notified',
        ]


@award.doc_type
class AwardDoc(Document):
    tender_title = fields.TextField(
        attr='tender.title',
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}
    )
    vendors_name = fields.TextField(
        attr='get_vendors',
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}

    )
    value = fields.TextField(
        attr="convert_value_to_string",
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}
    )

    class Django:
        model = Award
        fields = [
            'currency',
        ]


@tender_document.doc_type
class TenderDocumentDoc(Document):
    reference = fields.KeywordField(attr='tender.reference')

    content = fields.TextField(
        analyzer=case_insensitive_analyzer,
        fielddata=True,
        attr='content',
        fields={'raw': fields.KeywordField(
            multi=True, ignore_above=256,
            normalizer=case_insensitive_normalizer
        )}
    )

    class Django:
        model = TenderDocument
        fields = [
            'name',
            'download_url',
        ]
