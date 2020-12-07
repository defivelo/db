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

from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic.base import RedirectView

from .views import (
    AnnualStateSettingCreateView,
    AnnualStateSettingsListView,
    AnnualStateSettingUpdateView,
    InvoiceCreateView,
    InvoiceDetailView,
    InvoiceListView,
    InvoiceUpdateView,
    InvoiceYearlyListView,
    QualiCreateView,
    QualiDeleteView,
    QualiUpdateView,
    SeasonActorListView,
    SeasonAvailabilityUpdateView,
    SeasonAvailabilityView,
    SeasonCreateView,
    SeasonDeleteView,
    SeasonDetailView,
    SeasonErrorsListView,
    SeasonExportView,
    SeasonHelperListView,
    SeasonListView,
    SeasonOrgaListView,
    SeasonPersonalPlanningExportFeed,
    SeasonPersonalPlanningExportView,
    SeasonPlanningExportView,
    SeasonPlanningView,
    SeasonStaffChoiceUpdateView,
    SeasonToOpenView,
    SeasonToRunningView,
    SeasonUpdateView,
    SessionCreateView,
    SessionDeleteView,
    SessionDetailView,
    SessionExportView,
    SessionsListView,
    SessionStaffChoiceView,
    SessionUpdateView,
)

urlpatterns = [
    # Settings
    url(
        "^settings/y(?P<year>[0-9]{4})/",
        include(
            [
                url(
                    r"^(?P<pk>[0-9]+)/$",
                    never_cache(AnnualStateSettingUpdateView.as_view()),
                    name="annualstatesetting-update",
                ),
                url(
                    "^new/$",
                    never_cache(AnnualStateSettingCreateView.as_view()),
                    name="annualstatesetting-create",
                ),
                url(
                    "^$",
                    never_cache(AnnualStateSettingsListView.as_view()),
                    name="annualstatesettings-list",
                ),
            ]
        ),
    ),
    # Seasons
    url(
        r"^$",
        RedirectView.as_view(
            url=reverse_lazy("season-list", kwargs={"year": timezone.now().year}),
            permanent=False,
        ),
        name="season-list",
    ),
    url(
        r"^y(?P<year>[0-9]{4})/",
        include(
            [
                url(
                    r"^invoices/$",
                    never_cache(InvoiceYearlyListView.as_view()),
                    name="invoices-yearly-list",
                ),
                url(r"^$", never_cache(SeasonListView.as_view()), name="season-list"),
            ]
        ),
    ),
    url(r"^new/$", SeasonCreateView.as_view(), name="season-create"),
    url(
        r"^(?P<pk>[0-9]+)/",
        include(
            [
                url(r"^update/$", SeasonUpdateView.as_view(), name="season-update"),
                url(
                    r"^running-planning/$",
                    SeasonToRunningView.as_view(),
                    name="season-set-running",
                ),
                url(
                    r"^open-planning/$",
                    SeasonToOpenView.as_view(),
                    name="season-set-open",
                ),
                url(
                    r"^$",
                    never_cache(SeasonDetailView.as_view()),
                    name="season-detail",
                ),
                url(
                    r"^(?P<format>[a-z]+)export$",
                    never_cache(SeasonExportView.as_view()),
                    name="season-export",
                ),
                url(
                    r"^(?P<format>[a-z]+)exportplanning$",
                    never_cache(SeasonPlanningExportView.as_view()),
                    name="season-planning-export",
                ),
                url(
                    r"^moniteurs/$",
                    never_cache(SeasonHelperListView.as_view()),
                    name="season-helperlist",
                ),
                url(
                    r"^intervenants/$",
                    never_cache(SeasonActorListView.as_view()),
                    name="season-actorlist",
                ),
                url(
                    r"^erreurs/$",
                    never_cache(SeasonErrorsListView.as_view()),
                    name="season-errorslist",
                ),
                url(
                    r"^availability/$",
                    never_cache(SeasonAvailabilityView.as_view()),
                    name="season-availabilities",
                ),
                url(
                    r"^planning/(?P<helperpk>[0-9]+)/",
                    include(
                        [
                            url(
                                "^$",
                                never_cache(SeasonPlanningView.as_view()),
                                name="season-planning",
                            ),
                            url(
                                "^(?P<format>[a-z]+)exportplanning$",
                                never_cache(SeasonPersonalPlanningExportView.as_view()),
                                name="season-personal-planning-export",
                            ),
                            url(
                                r"^feed.ics$",
                                SeasonPersonalPlanningExportFeed(),
                                name="season-personal-calendar",
                            ),
                        ]
                    ),
                ),
                url(
                    r"^availability/staff/$",
                    never_cache(SeasonStaffChoiceUpdateView.as_view()),
                    name="season-staff-update",
                ),
                url(
                    r"^availability/(?P<helperpk>[0-9]+)/$",
                    SeasonAvailabilityUpdateView.as_view(),
                    name="season-availabilities-update",
                ),
                url(
                    r"^delete/$",
                    SeasonDeleteView.as_view(),
                    name="season-delete",
                ),
            ]
        ),
    ),
    # Invoices
    url(
        r"^(?P<seasonpk>[0-9]+)/",
        include(
            [
                url(
                    "invoices/",
                    never_cache(SeasonOrgaListView.as_view()),
                    name="invoice-orga-list",
                ),
                url(
                    r"i(?P<orgapk>[0-9]+)/",
                    include(
                        [
                            url(
                                r"^new/$",
                                never_cache(InvoiceCreateView.as_view()),
                                name="invoice-create",
                            ),
                            url(
                                r"^list/$",
                                never_cache(InvoiceListView.as_view()),
                                name="invoice-list",
                            ),
                            url(
                                r"^(?P<invoiceref>.+)/edit/$",
                                never_cache(InvoiceUpdateView.as_view()),
                                name="invoice-update",
                            ),
                            url(
                                r"^(?P<invoiceref>.+)/$",
                                never_cache(InvoiceDetailView.as_view()),
                                name="invoice-detail",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # Sessions
    url(
        r"^(?P<seasonpk>[0-9]+)/(?P<year>[0-9]{4})/w(?P<week>[0-9]+)/$",
        never_cache(SessionsListView.as_view()),
        name="session-list",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/snew/$",
        never_cache(SessionCreateView.as_view()),
        name="session-create",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/$",
        never_cache(SessionDetailView.as_view()),
        name="session-detail",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/(?P<format>[a-z]+)export$",
        never_cache(SessionExportView.as_view()),
        name="session-export",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/availability/$",
        never_cache(SessionStaffChoiceView.as_view()),
        name="session-staff-choices",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/update/$",
        SessionUpdateView.as_view(),
        name="session-update",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/delete/$",
        SessionDeleteView.as_view(),
        name="session-delete",
    ),
    # Qualis
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/quali$",
        never_cache(QualiCreateView.as_view()),
        name="quali-create",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/$",
        never_cache(QualiUpdateView.as_view()),
        name="quali-update",
    ),
    url(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/delete$",
        QualiDeleteView.as_view(),
        name="quali-delete",
    ),
]
