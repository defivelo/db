from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0008_merge_WS_in_VS'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='address_ofs_no',
            field=models.CharField(verbose_name='Commune OFS', max_length=4,
                                blank=True)
        ),
        migrations.AddField(
            model_name='address',
            name='address_country',
            field=django_countries.fields.CountryField(default='CH', max_length=2,
                                                       verbose_name='Pays'),
        )
    ]
