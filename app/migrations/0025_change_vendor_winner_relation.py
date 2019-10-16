# Generated by Django 2.2.4 on 2019-10-07 15:07

from django.db import migrations, models

def move_vendors_link(apps, schema_editor):
    vendor_model = apps.get_model('app', 'Vendor')
    winner_model = apps.get_model('app', 'Winner')
    for winner in winner_model.objects.all():
        vendor = winner.vendor
        winner.vendors.add(vendor)
        winner.save()

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_split_winner_vendor'),
    ]

    operations = [

        migrations.RunPython(move_vendors_link),
        migrations.RemoveField(
            model_name='winner',
            name='vendor',
        ),
        migrations.AddField(
            model_name='winner',
            name='vendors',
            field=models.ManyToManyField(related_name='winners', to='app.Vendor'),
        ),
    ]
