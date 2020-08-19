from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.db import migrations, models

def mulitify_actors(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    UserProfile = apps.get_model('user', 'UserProfile')
    for up in UserProfile.objects.all():
        if up.actor_for:
            up.actor_for_multi.add(up.actor_for)

def demulitify_actors(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    UserProfile = apps.get_model('user', 'UserProfile')
    for up in UserProfile.objects.exclude(actor_for_multi=None):
        up.actor_for = up.actor_for_multi.first()
        up.save()


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0037_auto_20170822_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='actor_for_multi',
            field=models.ManyToManyField(blank=True, null=True, related_name='actors_multi', to='challenge.QualificationActivity', verbose_name='Intervenant'),
        ),
        migrations.RunPython(mulitify_actors,
                             demulitify_actors),
    ]
