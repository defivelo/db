# Generated by Django 2.2.9 on 2020-03-04 14:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='orga.Organization', verbose_name='Établissement'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='ref',
            field=models.CharField(max_length=20, unique=True, verbose_name='Référence'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='season',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='challenge.Season', verbose_name='Saison'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='title',
            field=models.CharField(blank=True, max_length=255, verbose_name='Titre'),
        ),
    ]
