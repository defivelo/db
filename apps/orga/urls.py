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

from django.urls import re_path
from django.views.decorators.cache import never_cache

from .views import (
    OrganizationAutocomplete,
    OrganizationCreateView,
    OrganizationDetailView,
    OrganizationListExport,
    OrganizationsListView,
    OrganizationUpdateView,
)

urlpatterns = [
    re_path(
        r"^$", never_cache(OrganizationsListView.as_view()), name="organization-list"
    ),
    re_path(
        r"^(?P<void>)?(?P<format>[a-z]+)export/$",
        never_cache(OrganizationListExport.as_view()),
        name="organization-list-export",
    ),
    re_path(r"^new/$", OrganizationCreateView.as_view(), name="organization-create"),
    re_path(
        r"^(?P<pk>[0-9]+)/$",
        never_cache(OrganizationDetailView.as_view()),
        name="organization-detail",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/update/$",
        OrganizationUpdateView.as_view(),
        name="organization-update",
    ),
    re_path(
        r"^autocomplete/$",
        OrganizationAutocomplete.as_view(),
        name="organization-autocomplete",
    ),
]
