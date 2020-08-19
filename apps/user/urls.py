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

from django.conf.urls import include, url
from django.views.decorators.cache import never_cache

from .views import (
    ResendUserCredentials,
    SendUserCredentials,
    UserAssignRole,
    UserCreate,
    UserDetail,
    UserList,
    UserListExport,
    UserUpdate,
)
from .views.actions import MarkInactive
from .views.autocomplete import (
    Actors,
    AllCoordinators,
    AllPersons,
    Helpers,
    Leaders,
    PersonsRelevantForSessions,
)
from .views.deletes import UserDelete

urlpatterns = [
    url(r"^$", never_cache(UserList.as_view()), name="user-list"),
    url(
        r"^(?P<void>)?(?P<format>[a-z]+)export/$",
        never_cache(UserListExport.as_view()),
        name="user-list-export",
    ),
    url(r"^new/$", UserCreate.as_view(), name="user-create"),
    url(r"^me/$", never_cache(UserDetail.as_view()), name="profile-detail"),
    url(r"^(?P<pk>[0-9]+)/$", never_cache(UserDetail.as_view()), name="user-detail"),
    url(
        r"^(?P<pk>[0-9]+)/sendcreds/$",
        never_cache(SendUserCredentials.as_view()),
        name="user-sendcredentials",
    ),
    url(
        r"^(?P<pk>[0-9]+)/resendcreds/$",
        never_cache(ResendUserCredentials.as_view()),
        name="user-resendcredentials",
    ),
    url(
        r"^(?P<pk>[0-9]+)/delete/$",
        never_cache(UserDelete.as_view()),
        name="user-delete",
    ),
    url(
        r"^(?P<pk>[0-9]+)/assign_role/$",
        never_cache(UserAssignRole.as_view()),
        name="user-assign-role",
    ),
    url(
        r"^actions/",
        include(
            [
                url(
                    r"^mark-inactive$",
                    never_cache(MarkInactive.as_view()),
                    name="users-actions-markinactive",
                ),
            ]
        ),
    ),
    url(r"^(?P<pk>[0-9]+)/update/$", UserUpdate.as_view(), name="user-update"),
    url(r"^ac/all/$", AllPersons.as_view(), name="user-AllPersons-ac"),
    url(r"^ac/coordinator/$", AllCoordinators.as_view(), name="user-coordinators"),
    url(
        r"^ac/prfs/$",
        PersonsRelevantForSessions.as_view(),
        name="user-PersonsRelevantForSessions-ac",
    ),
    url(r"^ac/helpers/$", Helpers.as_view(), name="user-Helpers-ac"),
    url(r"^ac/leaders/$", Leaders.as_view(), name="user-Leaders-ac"),
    url(r"^ac/actors/$", Actors.as_view(), name="user-Actors-ac"),
]
