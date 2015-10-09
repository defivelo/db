# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic.base import RedirectView

from .views import (
    QualiCreateView, QualiDeleteView, QualiUpdateView, SeasonActorListView,
    SeasonAvailabilityUpdateView, SeasonAvailabilityView, SeasonCreateView,
    SeasonDeleteView, SeasonDetailView, SeasonHelperListView, SeasonListView,
    SeasonStaffChoiceUpdateView, SeasonUpdateView, SessionCreateView,
    SessionDeleteView, SessionDetailView, SessionsListView,
    SessionStaffChoiceView, SessionUpdateView,
)

urlpatterns = [
    # Seasons
    url(r'^$', RedirectView.as_view(
        url=reverse_lazy('season-list', kwargs={
            'year': timezone.now().year}),
        permanent=False
        ), name="season-list"),
    url(r'^y(?P<year>[0-9]{4})/$',
        never_cache(SeasonListView.as_view()),
        name='season-list'),
    url(r'^new/$', SeasonCreateView.as_view(), name="season-create"),
    url(r'^(?P<pk>[0-9]+)/update/$', SeasonUpdateView.as_view(),
        name="season-update"),
    url(r'^(?P<pk>[0-9]+)/$',
        never_cache(SeasonDetailView.as_view()),
        name='season-detail'),
    url(r'^(?P<pk>[0-9]+)/moniteurs/$',
        SeasonHelperListView.as_view(),
        name='season-helperlist'),
    url(r'^(?P<pk>[0-9]+)/intervenants/$',
        SeasonActorListView.as_view(),
        name='season-actorlist'),
    url(r'^(?P<pk>[0-9]+)/availability/$',
        SeasonAvailabilityView.as_view(),
        name='season-availabilities'),
    url(r'^(?P<pk>[0-9]+)/availability/staff/$',
        SeasonStaffChoiceUpdateView.as_view(),
        name='season-staff-update'),
    url(r'^(?P<pk>[0-9]+)/availability/(?P<helperpk>[0-9]+)/edit/$',
        SeasonAvailabilityUpdateView.as_view(),
        name='season-availabilities-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', SeasonDeleteView.as_view(),
        name="season-delete"),

    # Sessions
    url(r'^(?P<seasonpk>[0-9]+)/(?P<year>[0-9]{4})/w(?P<week>[0-9]+)/$',
        SessionsListView.as_view(),
        name="session-list"),
    url(r'^(?P<seasonpk>[0-9]+)/snew/$', SessionCreateView.as_view(), name="session-create"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/$', SessionDetailView.as_view(),
        name="session-detail"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/availability/$',
        SessionStaffChoiceView.as_view(),
        name="session-staff-choices"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/update/$', SessionUpdateView.as_view(),
        name="session-update"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/delete/$', SessionDeleteView.as_view(),
        name="session-delete"),

    # Qualis
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/quali$', QualiCreateView.as_view(),
        name="quali-create"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/$',
        QualiUpdateView.as_view(), name="quali-update"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/delete$',
        QualiDeleteView.as_view(), name="quali-delete"),
]
