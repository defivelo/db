from __future__ import unicode_literals

from django.db import models, migrations

def migrate_addresses(apps, schema_editor):
    Address = apps.get_model("common", "Address")
    UserProfile = apps.get_model("user", "UserProfile")
    for up in UserProfile.objects.all():
        ad = Address.objects.create(
             address_street=up.address_street,
             address_no=up.address_no,
             address_zip=up.address_zip,
             address_city=up.address_city,
             address_canton=up.address_canton)
        up.address_ptr = ad
        up.save()

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_userprofile_address'),
    ]

    operations = [
        migrations.RunPython(migrate_addresses)
    ]
