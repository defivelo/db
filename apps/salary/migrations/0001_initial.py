# Generated by Django 2.2.9 on 2020-03-04 08:31

import apps.common.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Timesheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Date')),
                ('time_monitor', models.FloatField(blank=True, null=True, verbose_name='Heure moniteur')),
                ('time_actor', models.FloatField(blank=True, null=True, verbose_name='Heure intervenant')),
                ('overtime', models.FloatField(default=0, verbose_name='Heures supplémentaires')),
                ('traveltime', models.FloatField(default=0, verbose_name='Heures de trajet')),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('comments', models.TextField(blank=True, verbose_name='Remarques')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timesheets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'date')},
            },
        ),
    ]
