# Generated by Django 2.2.4 on 2019-09-11 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_auto_20190911_1321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='success',
        ),
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.CharField(blank=True, default='processing', max_length=255, null=True),
        ),
    ]