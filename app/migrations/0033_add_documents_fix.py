# Generated by Django 2.2.28 on 2022-11-21 15:30

from django.db import migrations
from app.management.commands.add_documents import Command


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0032_add_verbose_names'),
    ]

    operations = [
        migrations.RunPython(Command().handle, reverse)
    ]
