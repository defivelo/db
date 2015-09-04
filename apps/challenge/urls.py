# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.generic.base import RedirectView

from .views import (
    QualiCreateView, QualiDeleteView, QualiUpdateView, SessionCreateView,
    SessionDeleteView, SessionDetailView, SessionsListView, SessionUpdateView,
)

urlpatterns = [
    url(r'^$', RedirectView.as_view(
        url=reverse_lazy('session-list', kwargs={
            'year': timezone.now().year,
            'week': timezone.now().strftime('%W')}),
        permanent=False
        ), name="session-list"),
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
    url(r'^(?P<session>[0-9]+)/quali$', QualiCreateView.as_view(),
        name="quali-create"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/$',
        QualiUpdateView.as_view(), name="quali-update"),
    url(r'^(?P<session>[0-9]+)/quali/(?P<pk>[0-9]+)/delete$',
        QualiDeleteView.as_view(), name="quali-delete"),
]
