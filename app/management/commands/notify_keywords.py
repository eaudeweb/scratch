from app.management.commands.base.notify import BaseNotifyCommand
from app.management.commands.base.params import BaseParamsUI
from app.models import Tender


class Command(BaseNotifyCommand, BaseParamsUI):
    help = 'Notifies all users about tenders which contain one or more keywords'

    def notification_type(self):
        return 'Keyword'

    def get_tenders(self):
        return Tender.objects.filter(has_keywords=True).order_by('-published')
