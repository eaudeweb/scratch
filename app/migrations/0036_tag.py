# Generated by Django 4.1.4 on 2023-01-05 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0035_award_renewal_notified'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
    ]