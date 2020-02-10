from django.db import models


class LowerCharField(models.CharField):

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            value = value.lower()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)
