# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .views import HomeView

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^challenge/', include('apps.challenge.urls')),
    url(r'^orga/', include('apps.orga.urls')),
    url(r'^me/', include('apps.user.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

admin.site.site_header = _('DB Défi Vélo')
