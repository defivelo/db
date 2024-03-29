# Generated by Django 3.2.14 on 2022-07-14 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0080_auto_20220419_1025'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalannualstatesetting',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Configuration cantonale par année', 'verbose_name_plural': 'historical Configurations cantonales par année'},
        ),
        migrations.AlterModelOptions(
            name='historicalhelperseasonworkwish',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical helper season work wish', 'verbose_name_plural': 'historical helper season work wishs'},
        ),
        migrations.AlterModelOptions(
            name='historicalhelpersessionavailability',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Disponibilité par session', 'verbose_name_plural': 'historical Disponibilités par session'},
        ),
        migrations.AlterModelOptions(
            name='historicalqualification',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Qualif’', 'verbose_name_plural': 'historical Qualifs'},
        ),
        migrations.AlterModelOptions(
            name='historicalqualificationactivity',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Poste', 'verbose_name_plural': 'historical Postes'},
        ),
        migrations.AlterModelOptions(
            name='historicalseason',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Mois', 'verbose_name_plural': 'historical Mois'},
        ),
        migrations.AlterModelOptions(
            name='historicalsession',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical Session', 'verbose_name_plural': 'historical Sessions'},
        ),
        migrations.AlterField(
            model_name='historicalannualstatesetting',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalhelperseasonworkwish',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalhelpersessionavailability',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalqualification',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalqualificationactivity',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalseason',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalsession',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]
