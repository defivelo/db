# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic.base import RedirectView

from .views import (
    QualiCreateView, QualiDeleteView, QualiUpdateView, SeasonActorListView, SeasonAvailabilityUpdateView,
    SeasonAvailabilityView, SeasonCreateView, SeasonDeleteView, SeasonDetailView, SeasonErrorsListView,
    SeasonExportView, SeasonHelperListView, SeasonListView, SeasonPlanningExportView, SeasonStaffChoiceUpdateView,
    SeasonUpdateView, SessionCreateView, SessionDeleteView, SessionDetailView, SessionExportView, SessionsListView,
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
    url(r'^(?P<pk>[0-9]+)/(?P<format>[a-z]+)export$',
        never_cache(SeasonExportView.as_view()),
        name='season-export'),
    url(r'^(?P<pk>[0-9]+)/(?P<format>[a-z]+)exportplanning$',
        never_cache(SeasonPlanningExportView.as_view()),
        name='season-planning-export'),
    url(r'^(?P<pk>[0-9]+)/moniteurs/$',
        never_cache(SeasonHelperListView.as_view()),
        name='season-helperlist'),
    url(r'^(?P<pk>[0-9]+)/intervenants/$',
        never_cache(SeasonActorListView.as_view()),
        name='season-actorlist'),
    url(r'^(?P<pk>[0-9]+)/erreurs/$',
        never_cache(SeasonErrorsListView.as_view()),
        name='season-errorslist'),
    url(r'^(?P<pk>[0-9]+)/availability/$',
        never_cache(SeasonAvailabilityView.as_view()),
        name='season-availabilities'),
    url(r'^(?P<pk>[0-9]+)/availability/staff/$',
        never_cache(SeasonStaffChoiceUpdateView.as_view()),
        name='season-staff-update'),
    url(r'^(?P<pk>[0-9]+)/availability/(?P<helperpk>[0-9]+)/$',
        SeasonAvailabilityUpdateView.as_view(),
        name='season-availabilities-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', SeasonDeleteView.as_view(),
        name="season-delete"),

    # Sessions
    url(r'^(?P<seasonpk>[0-9]+)/(?P<year>[0-9]{4})/w(?P<week>[0-9]+)/$',
        never_cache(SessionsListView.as_view()),
        name="session-list"),
    url(r'^(?P<seasonpk>[0-9]+)/snew/$',
        never_cache(SessionCreateView.as_view()),
        name="session-create"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/$',
        never_cache(SessionDetailView.as_view()),
        name="session-detail"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/(?P<format>[a-z]+)export$',
        never_cache(SessionExportView.as_view()),
        name='session-export'),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/availability/$',
        never_cache(SessionStaffChoiceView.as_view()),
        name="session-staff-choices"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/update/$',
        SessionUpdateView.as_view(), name="session-update"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/delete/$',
        SessionDeleteView.as_view(), name="session-delete"),

    # Qualis
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/quali$',
        never_cache(QualiCreateView.as_view()), name="quali-create"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/$',
        never_cache(QualiUpdateView.as_view()), name="quali-update"),
    url(r'^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/delete$',  # NOQA
        QualiDeleteView.as_view(), name="quali-delete"),
]
