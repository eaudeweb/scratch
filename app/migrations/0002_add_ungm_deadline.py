# Generated by Django 2.2.3 on 2019-07-16 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tender',
            name='deadline',
            field=models.DateTimeField(),
        ),
    ]
