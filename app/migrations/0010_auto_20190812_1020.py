# Generated by Django 2.2.4 on 2019-08-12 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20190805_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='tender',
            name='cpv_codes',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='tender',
            name='unspsc_codes',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
