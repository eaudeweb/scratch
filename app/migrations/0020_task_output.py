# Generated by Django 2.2.4 on 2019-09-11 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_auto_20190911_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='output',
            field=models.TextField(blank=True, max_length=5055, null=True),
        ),
    ]