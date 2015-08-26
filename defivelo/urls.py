# -*- coding: utf-8 -*-
from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .views import HomeView

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

admin.site.site_header = _('DB Défi Vélo')
