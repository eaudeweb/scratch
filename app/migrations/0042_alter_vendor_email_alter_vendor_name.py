# Generated by Django 4.1.4 on 2023-01-12 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0041_vendor_comment_vendor_contact_name_vendor_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
