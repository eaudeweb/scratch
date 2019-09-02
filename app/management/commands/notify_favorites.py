from app.management.commands.base.notify import BaseNotifyCommand
from app.models import Tender


class Command(BaseNotifyCommand):
    def notification_type(self):
        return 'Favorite'

    def get_tenders(self):
        tenders = Tender.objects.filter(favourite=True, source='UNGM')
        return tenders
