# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.generic.base import RedirectView

from .views import (
    QualiCreateView, QualiDeleteView, QualiUpdateView, SeasonCreateView,
    SeasonDeleteView, SeasonDetailView, SeasonListView, SeasonUpdateView,
    SessionCreateView, SessionDeleteView, SessionDetailView, SessionsListView,
    SessionUpdateView,
)

urlpatterns = [
    # Catchall
    url(r'^$', RedirectView.as_view(
        url=reverse_lazy('session-list', kwargs={
            'year': timezone.now().year,
            'week': timezone.now().strftime('%W')}),
        permanent=False
        ), name="session-list"),

    # Seasons
    url(r'^season/$', RedirectView.as_view(
        url=reverse_lazy('season-list', kwargs={
            'year': timezone.now().year}),
        permanent=False
        ), name="season-list"),
    url(r'^season/y(?P<year>[0-9]{4})/$',
        SeasonListView.as_view(),
        name='season-list'),
    url(r'^season/new/$', SeasonCreateView.as_view(), name="season-create"),
    url(r'^season/(?P<pk>[0-9]+)/update/$', SeasonUpdateView.as_view(),
        name="season-update"),
    url(r'^season/(?P<pk>[0-9]+)/$',
        SeasonDetailView.as_view(),
        name='season-detail'),
    url(r'^season/(?P<pk>[0-9]+)/delete/$', SeasonDeleteView.as_view(),
        name="season-delete"),
    # Sessions
    url(r'^y(?P<year>[0-9]{4})/w(?P<week>[0-9]+)/$',
        SessionsListView.as_view(),
        name="session-list"),
    url(r'^new/$', SessionCreateView.as_view(), name="session-create"),
    url(r'^(?P<pk>[0-9]+)/$', SessionDetailView.as_view(),
        name="session-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', SessionUpdateView.as_view(),
        name="session-update"),
    url(r'^(?P<pk>[0-9]+)/delete/$', SessionDeleteView.as_view(),
        name="session-delete"),
    # Qualis
    url(r'^(?P<session>[0-9]+)/quali$', QualiCreateView.as_view(),
        name="quali-create"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/$',
        QualiUpdateView.as_view(), name="quali-update"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/delete$',
        QualiDeleteView.as_view(), name="quali-delete"),
]
