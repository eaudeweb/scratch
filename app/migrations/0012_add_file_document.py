# Generated by Django 2.2.4 on 2019-08-23 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20190822_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenderdocument',
            name='document',
            field=models.FileField(default=1, upload_to='static/documents'),
            preserve_default=False,
        ),
    ]
