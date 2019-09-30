from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        from app.signals import set_keywords
        post_save.connect(set_keywords, sender='app.Keyword', dispatch_uid="keyword_save")
        post_delete.connect(set_keywords, sender='app.Keyword', dispatch_uid="keyword_delete")
