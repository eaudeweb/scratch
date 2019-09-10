from app.management.commands.base.notify import BaseNotifyCommand
from app.management.commands.base.params import BaseParamsUI
from app.models import Tender


class Command(BaseNotifyCommand, BaseParamsUI):
    help = 'Notifies all users about favorite tenders updates'

    def notification_type(self):
        return 'Favorite'

    def get_tenders(self):
        tenders = Tender.objects.filter(favourite=True)
        return tenders
