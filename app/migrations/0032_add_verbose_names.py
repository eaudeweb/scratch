# Generated by Django 2.2.28 on 2022-11-11 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0031_auto_20200225_1327'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cpvcode',
            options={'verbose_name': 'CPV code', 'verbose_name_plural': 'CPV codes'},
        ),
        migrations.AlterModelOptions(
            name='tedcountry',
            options={'verbose_name': 'TED country', 'verbose_name_plural': 'TED countries'},
        ),
        migrations.AlterModelOptions(
            name='unspsccode',
            options={'verbose_name': 'UNSPC code', 'verbose_name_plural': 'UNSPC codes'},
        ),
    ]
