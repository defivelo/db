# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-11 14:11

"""
Replaces migrations from `simple-article==0.2.1`
"""

from __future__ import unicode_literals

from django.db import migrations, models
from django.utils import timezone

import taggit.managers
import tinymce.models


# fmt: off


class Migration(migrations.Migration):

    replaces = [('article', '0001_initial'), ('article', '0002_article_tags')]

    initial = True

    dependencies = [
        ('taggit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('slug', models.SlugField(unique=True, max_length=255, verbose_name='Slug', blank=True)),
                ('summary', models.TextField(null=True, verbose_name='Summary', blank=True)),
                ('image', models.ImageField(upload_to='articles/%Y/%m/%d', null=True, verbose_name='Image', blank=True)),
                ('modified', models.DateTimeField(default=timezone.now, verbose_name='Modified')),
                ('published', models.BooleanField(default=False)),
                ('body', tinymce.models.HTMLField(verbose_name='Body')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags'))
            ],
            options={
                'ordering': ['-modified'],
                'verbose_name': 'Article',
            },
        ),
    ]

# fmt: on
