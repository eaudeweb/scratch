# Generated by Django 2.2.4 on 2019-08-22 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20190812_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tender',
            name='description',
            field=models.TextField(blank=True, max_length=5059, null=True),
        ),
    ]
