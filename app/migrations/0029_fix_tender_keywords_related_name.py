# Generated by Django 2.2.9 on 2020-02-07 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_make_keywords_lowercase'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tender',
            name='keywords',
            field=models.ManyToManyField(blank=True, related_name='tenders', to='app.Keyword'),
        ),
    ]