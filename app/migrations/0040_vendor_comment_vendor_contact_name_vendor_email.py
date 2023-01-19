# Generated by Django 4.1.4 on 2023-01-09 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0039_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='contact_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]
