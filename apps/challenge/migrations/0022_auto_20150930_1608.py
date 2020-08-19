from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0021_auto_20150917_1730'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='chosen_staff',
            field=models.ManyToManyField(related_name='sessions', blank=True, verbose_name='Personnel', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_A',
            field=models.ForeignKey(null=True, related_name='qualifs_A', to='challenge.QualificationActivity', blank=True, verbose_name='Vélo dans la rue', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_B',
            field=models.ForeignKey(null=True, related_name='qualifs_B', to='challenge.QualificationActivity', blank=True, verbose_name='Mécanique', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_C',
            field=models.ForeignKey(null=True, related_name='qualifs_C', to='challenge.QualificationActivity', blank=True, verbose_name='Rencontre', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='actor',
            field=models.ForeignKey(null=True, related_name='qualifs_actor', to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Intervenant', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='helpers',
            field=models.ManyToManyField(related_name='qualifs_mon1', blank=True, verbose_name='Moniteurs 1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='leader',
            field=models.ForeignKey(null=True, related_name='qualifs_mon2', to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Moniteur 2', on_delete=models.CASCADE),
        ),
    ]
