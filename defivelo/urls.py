# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, patterns, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .views import HomeView, LicenseView

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^license/', LicenseView.as_view(), name='license'),
    url(r'^agpl-', include('django_agpl.urls')),
)

urlpatterns += i18n_patterns(
    '',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^season/', include('apps.challenge.urls')),
    url(r'^orga/', include('apps.orga.urls')),
    url(r'^user/', include('apps.user.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
)

admin.site.site_header = _('DB Défi Vélo')
