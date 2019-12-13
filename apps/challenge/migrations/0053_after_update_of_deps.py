# Generated by Django 2.2.8 on 2019-12-12 13:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import parler.fields


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0052_auto_20190225_1631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='helperseasonworkwish',
            name='helper',
            field=models.ForeignKey(limit_choices_to={'profile__isnull': False}, on_delete=django.db.models.deletion.CASCADE, related_name='work_wishes', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur'),
        ),
        migrations.AlterField(
            model_name='helpersessionavailability',
            name='helper',
            field=models.ForeignKey(limit_choices_to={'profile__isnull': False}, on_delete=django.db.models.deletion.CASCADE, related_name='availabilities', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur'),
        ),
        migrations.AlterField(
            model_name='historicalhelperseasonworkwish',
            name='helper',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'profile__isnull': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur'),
        ),
        migrations.AlterField(
            model_name='historicalhelpersessionavailability',
            name='helper',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'profile__isnull': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur'),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='activity_A',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'category': 'A'}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='challenge.QualificationActivity', verbose_name='Agilité'),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='activity_B',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'category': 'B'}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='challenge.QualificationActivity', verbose_name='Mécanique'),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='activity_C',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'category': 'C'}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='challenge.QualificationActivity', verbose_name='Rencontre'),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='actor',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'profile__actor_for__isnull': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Intervenant'),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='leader',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to=models.Q(profile__formation='M2'), null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur 2'),
        ),
        migrations.AlterField(
            model_name='historicalseason',
            name='leader',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'managedstates__isnull': False}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Chargé de projet'),
        ),
        migrations.AlterField(
            model_name='historicalsession',
            name='orga',
            field=models.ForeignKey(blank=True, db_constraint=False, limit_choices_to={'address_canton__isnull': False, 'status__in': [10]}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='orga.Organization', verbose_name='Établissement'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_A',
            field=models.ForeignKey(blank=True, limit_choices_to={'category': 'A'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_A', to='challenge.QualificationActivity', verbose_name='Agilité'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_B',
            field=models.ForeignKey(blank=True, limit_choices_to={'category': 'B'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_B', to='challenge.QualificationActivity', verbose_name='Mécanique'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_C',
            field=models.ForeignKey(blank=True, limit_choices_to={'category': 'C'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_C', to='challenge.QualificationActivity', verbose_name='Rencontre'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='actor',
            field=models.ForeignKey(blank=True, limit_choices_to={'profile__actor_for__isnull': False}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_actor', to=settings.AUTH_USER_MODEL, verbose_name='Intervenant'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='helpers',
            field=models.ManyToManyField(blank=True, limit_choices_to=models.Q(profile__formation__in=['M1', 'M2']), related_name='qualifs_mon1', to=settings.AUTH_USER_MODEL, verbose_name='Moniteurs 1'),
        ),
        migrations.AlterField(
            model_name='qualification',
            name='leader',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(profile__formation='M2'), null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qualifs_mon2', to=settings.AUTH_USER_MODEL, verbose_name='Moniteur 2'),
        ),
        migrations.AlterField(
            model_name='qualificationactivitytranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='challenge.QualificationActivity'),
        ),
        migrations.AlterField(
            model_name='season',
            name='leader',
            field=models.ForeignKey(limit_choices_to={'managedstates__isnull': False}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Chargé de projet'),
        ),
        migrations.AlterField(
            model_name='session',
            name='orga',
            field=models.ForeignKey(limit_choices_to={'address_canton__isnull': False, 'status__in': [10]}, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='orga.Organization', verbose_name='Établissement'),
        ),
    ]
