# Generated by Django 2.2.12 on 2020-10-26 14:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0065_auto_20200512_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceline',
            name='session',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='challenge.Session'),
        ),
    ]
