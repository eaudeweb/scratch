from app.management.commands.base.notify import BaseNotifyCommand
from app.management.commands.base.params import BaseParamsUI
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseNotifyCommand, BaseParamsUI):
    help = 'Notifies specific user about favorite tenders updates'

    def notification_type(self):
        return 'Favorite'

    def get_tenders(self):
        user_id = self.options["user_id"]
        user = User.objects.get(id=user_id)
        return user.favorite_tenders.order_by('-published')
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('user_id', type=int)
