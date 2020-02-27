# Generated by Django 2.2.9 on 2020-03-04 14:25

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('challenge', '0055_annualstatesetting_historicalannualstatesetting'),
        ('orga', '0006_auto_20170831_1201'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.IntegerField(choices=[(0, 'Brouillon'), (1, 'Validée')], default=0)),
                ('ref', models.CharField(max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='orga.Organization')),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='challenge.Season')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nb_bikes', models.PositiveSmallIntegerField()),
                ('nb_participants', models.PositiveSmallIntegerField()),
                ('cost_bikes', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0)])),
                ('cost_participants', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(0)])),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoices.Invoice')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='challenge.Session')),
            ],
        ),
    ]
