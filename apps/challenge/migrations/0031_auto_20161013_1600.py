from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0030_auto_20161010_1519'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='qualification',
            options={'verbose_name': "Qualif'", 'verbose_name_plural': 'Qualifs', 'ordering': ['session', 'created_on', 'name']},
        ),
        migrations.AlterField(
            model_name='qualification',
            name='activity_A',
            field=models.ForeignKey(verbose_name='Vélo urbain', to='challenge.QualificationActivity', blank=True, null=True, related_name='qualifs_A', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='qualificationactivity',
            name='category',
            field=models.CharField(max_length=1, verbose_name='Catégorie', choices=[('A', 'Vélo urbain'), ('B', 'Mécanique'), ('C', 'Rencontre')], blank=True),
        ),
    ]
