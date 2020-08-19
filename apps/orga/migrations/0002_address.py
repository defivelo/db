from __future__ import unicode_literals

from django.db import models, migrations


def migrate_addresses(apps, schema_editor):
    # We can't import the Address model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Address = apps.get_model("common", "Address")
    Organization = apps.get_model("orga", "Organization")
    for orga in Organization.objects.all():
        ad = Address.objects.create(
             address_street=orga.address_street,
             address_no=orga.address_no,
             address_zip=orga.address_zip,
             address_city=orga.address_city,
             address_canton=orga.address_canton)
        orga.address_ptr = ad
        orga.save()


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('orga', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='address_ptr',
            field=models.ForeignKey(to='common.Address', null=True, on_delete=models.CASCADE),
        ),
        migrations.RunPython(migrate_addresses),
        migrations.RemoveField(
            model_name='organization',
            name='id',
        ),
        migrations.AlterField(
            model_name='organization',
            name='address_ptr',
            field=models.OneToOneField(to='common.Address', auto_created=True, serialize=False, primary_key=True, parent_link=True, on_delete=models.CASCADE),
        ),
        migrations.RemoveField(
            model_name='organization',
            name='address_canton',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='address_city',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='address_no',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='address_street',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='address_zip',
        ),
    ]
