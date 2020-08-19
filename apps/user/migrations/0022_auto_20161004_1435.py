from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0021_remove_userprofile_office_member'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserManagedState',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('canton', models.CharField(max_length=2, verbose_name='Canton', choices=[('BS', 'Basel-Stadt'), ('BE', 'Berne'), ('FR', 'Fribourg'), ('GE', 'Geneva'), ('JU', 'Jura'), ('LU', 'Lucerne'), ('NE', 'Neuchatel'), ('SG', 'St. Gallen'), ('VS', 'Valais'), ('VD', 'Vaud'), ('ZH', 'Zurich')])),
                ('user', models.ForeignKey(related_name='managedstates', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Canton géré',
                'verbose_name_plural': 'Cantons gérés',
            },
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': 'Profil', 'verbose_name_plural': 'Profils'},
        ),
        migrations.AlterUniqueTogether(
            name='usermanagedstate',
            unique_together=set([('user', 'canton')]),
        ),
    ]
