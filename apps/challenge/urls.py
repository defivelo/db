# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    QualiCreateView, QualiDeleteView, QualiUpdateView, SessionCreateView,
    SessionDeleteView, SessionDetailView, SessionsListView, SessionUpdateView,
)

urlpatterns = [
    url(r'^$', SessionsListView.as_view(), name="session-list"),
    url(r'^new/$', SessionCreateView.as_view(), name="session-create"),
    url(r'^(?P<pk>[0-9]+)/$', SessionDetailView.as_view(),
        name="session-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', SessionUpdateView.as_view(),
        name="session-update"),
    url(r'^(?P<pk>[0-9]+)/delete/$', SessionDeleteView.as_view(),
        name="session-delete"),
    url(r'^(?P<session>[0-9]+)/quali$', QualiCreateView.as_view(), name="quali-create"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/$',
        QualiUpdateView.as_view(), name="quali-update"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/delete$',
        QualiDeleteView.as_view(), name="quali-delete"),
]
