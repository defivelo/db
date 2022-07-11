# Generated by Django 1.11.4 on 2017-08-24 09:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0036_auto_20170818_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qualification',
            name='activity_A',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_A', to='challenge.QualificationActivity', verbose_name='Vélo urbain'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_B',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_B', to='challenge.QualificationActivity', verbose_name='Mécanique'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_C',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_C', to='challenge.QualificationActivity', verbose_name='Rencontre'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='actor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_actor', to=settings.AUTH_USER_MODEL, verbose_name='Intervenant'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='leader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_mon2', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur 2'),
        ),
        migrations.AlterField(
            model_name='season',
            name='cantons',
            field=models.CharField(choices=[('AP', 'Appenzell'), ('BE', 'Berne'), ('BS', 'Basel-Stadt'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('VS-OW', 'Haut-Valais'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')], max_length=41, verbose_name='Cantons'),
        ),
        migrations.AlterField(
            model_name='session',
            name='superleader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sess_monplus', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur + / Photographe'),
        ),
    ]
