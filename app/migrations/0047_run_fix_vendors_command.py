# Generated by Django 4.1.4 on 2023-01-19 15:13

from django.db import migrations
from app.management.commands.fix_vendors import Command


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0046_user_favorites'),
    ]

    operations = [
        migrations.RunPython(Command().handle, reverse)
    ]
