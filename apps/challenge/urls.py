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

from django.conf.urls import include
from django.urls import re_path
from django.views.decorators.cache import never_cache

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
    SeasonDetailView,
    SeasonErrorsListView,
    SeasonExportView,
    SeasonHelperListView,
    SeasonListRedirect,
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
from .views.invoice import InvoiceListExport
from .views.registration import register, register_confirm, register_validate
from .views.session import SessionCloneView

urlpatterns = [
    # Settings
    re_path(
        "^settings/y(?P<year>[0-9]{4})/",
        include(
            [
                re_path(
                    r"^(?P<pk>[0-9]+)/$",
                    never_cache(AnnualStateSettingUpdateView.as_view()),
                    name="annualstatesetting-update",
                ),
                re_path(
                    "^new/$",
                    never_cache(AnnualStateSettingCreateView.as_view()),
                    name="annualstatesetting-create",
                ),
                re_path(
                    "^$",
                    never_cache(AnnualStateSettingsListView.as_view()),
                    name="annualstatesettings-list",
                ),
            ]
        ),
    ),
    # Seasons
    re_path(
        r"^$",
        SeasonListRedirect.as_view(),
        name="season-list",
    ),
    re_path(
        r"^y(?P<year>[0-9]{4})/",
        include(
            [
                re_path(
                    r"^invoices/$",
                    never_cache(InvoiceYearlyListView.as_view()),
                    name="invoices-yearly-list",
                ),
                re_path(
                    r"^invoices/(?P<void>)?(?P<format>[a-z]+)export/$",
                    never_cache(InvoiceListExport.as_view()),
                    name="invoices-yearly-list-export",
                ),
                re_path(
                    r"(?P<dv_season>[0-4]{1})/$",
                    never_cache(SeasonListView.as_view()),
                    name="season-list",
                ),
            ]
        ),
    ),
    re_path(r"^new/$", SeasonCreateView.as_view(), name="season-create"),
    re_path(
        r"^(?P<pk>[0-9]+)/",
        include(
            [
                re_path(r"^update/$", SeasonUpdateView.as_view(), name="season-update"),
                re_path(
                    r"^running-planning/$",
                    SeasonToRunningView.as_view(),
                    name="season-set-running",
                ),
                re_path(
                    r"^open-planning/$",
                    SeasonToOpenView.as_view(),
                    name="season-set-open",
                ),
                re_path(
                    r"^$",
                    never_cache(SeasonDetailView.as_view()),
                    name="season-detail",
                ),
                re_path(
                    r"^(?P<format>[a-z]+)export$",
                    never_cache(SeasonExportView.as_view()),
                    name="season-export",
                ),
                re_path(
                    r"^(?P<format>[a-z]+)exportplanning$",
                    never_cache(SeasonPlanningExportView.as_view()),
                    name="season-planning-export",
                ),
                re_path(
                    r"^moniteurs/$",
                    never_cache(SeasonHelperListView.as_view()),
                    name="season-helperlist",
                ),
                re_path(
                    r"^intervenants/$",
                    never_cache(SeasonActorListView.as_view()),
                    name="season-actorlist",
                ),
                re_path(
                    r"^erreurs/$",
                    never_cache(SeasonErrorsListView.as_view()),
                    name="season-errorslist",
                ),
                re_path(
                    r"^availability/$",
                    never_cache(SeasonAvailabilityView.as_view()),
                    name="season-availabilities",
                ),
                re_path(
                    r"^planning/(?P<helperpk>[0-9]+)/",
                    include(
                        [
                            re_path(
                                "^$",
                                never_cache(SeasonPlanningView.as_view()),
                                name="season-planning",
                            ),
                            re_path(
                                "^(?P<format>[a-z]+)exportplanning$",
                                never_cache(SeasonPersonalPlanningExportView.as_view()),
                                name="season-personal-planning-export",
                            ),
                            re_path(
                                r"^feed.ics$",
                                SeasonPersonalPlanningExportFeed(),
                                name="season-personal-calendar",
                            ),
                        ]
                    ),
                ),
                re_path(
                    r"^availability/staff/$",
                    never_cache(SeasonStaffChoiceUpdateView.as_view()),
                    name="season-staff-update",
                ),
                re_path(
                    r"^availability/(?P<helperpk>[0-9]+)/$",
                    SeasonAvailabilityUpdateView.as_view(),
                    name="season-availabilities-update",
                ),
            ]
        ),
    ),
    # Invoices
    re_path(
        r"^(?P<seasonpk>[0-9]+)/",
        include(
            [
                re_path(
                    "invoices/",
                    never_cache(SeasonOrgaListView.as_view()),
                    name="invoice-orga-list",
                ),
                re_path(
                    r"i(?P<orgapk>[0-9]+)/",
                    include(
                        [
                            re_path(
                                r"^new/$",
                                never_cache(InvoiceCreateView.as_view()),
                                name="invoice-create",
                            ),
                            re_path(
                                r"^list/$",
                                never_cache(InvoiceListView.as_view()),
                                name="invoice-list",
                            ),
                            re_path(
                                r"^(?P<invoiceref>.+)/edit/$",
                                never_cache(InvoiceUpdateView.as_view()),
                                name="invoice-update",
                            ),
                            re_path(
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
    re_path(
        r"^(?P<seasonpk>[0-9]+)/(?P<year>[0-9]{4})/w(?P<week>[0-9]+)/$",
        never_cache(SessionsListView.as_view()),
        name="session-list",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/snew/$",
        never_cache(SessionCreateView.as_view()),
        name="session-create",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/$",
        never_cache(SessionDetailView.as_view()),
        name="session-detail",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/(?P<format>[a-z]+)export$",
        never_cache(SessionExportView.as_view()),
        name="session-export",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/availability/$",
        never_cache(SessionStaffChoiceView.as_view()),
        name="session-staff-choices",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/update/$",
        SessionUpdateView.as_view(),
        name="session-update",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/clone/$",
        SessionCloneView.as_view(),
        name="session-clone",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<pk>[0-9]+)/delete/$",
        SessionDeleteView.as_view(),
        name="session-delete",
    ),
    # Qualis
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/quali$",
        never_cache(QualiCreateView.as_view()),
        name="quali-create",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/$",
        never_cache(QualiUpdateView.as_view()),
        name="quali-update",
    ),
    re_path(
        r"^(?P<seasonpk>[0-9]+)/s(?P<sessionpk>[0-9]+)/q(?P<pk>[0-9]+)/delete$",
        QualiDeleteView.as_view(),
        name="quali-delete",
    ),
    # Registrations
    re_path(r"^registration/$", register, name="registration-create"),
    re_path(r"^registration/confirm/$", register_confirm, name="registration-confirm"),
    re_path(
        r"^registrations/validate/$", register_validate, name="registration-validate"
    ),
]
