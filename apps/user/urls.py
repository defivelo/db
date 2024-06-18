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
    OfsAutoComplete,
    PersonsRelevantForSessions,
)
from .views.deletes import UserDelete

# from .views.autocomplete import get_form_field


urlpatterns = [
    re_path(r"^$", never_cache(UserList.as_view()), name="user-list"),
    re_path(
        r"^(?P<void>)?(?P<format>[a-z]+)export/$",
        never_cache(UserListExport.as_view()),
        name="user-list-export",
    ),
    re_path(r"^new/$", UserCreate.as_view(), name="user-create"),
    re_path(r"^me/$", never_cache(UserDetail.as_view()), name="profile-detail"),
    re_path(
        r"^(?P<pk>[0-9]+)/$", never_cache(UserDetail.as_view()), name="user-detail"
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/sendcreds/$",
        never_cache(SendUserCredentials.as_view()),
        name="user-sendcredentials",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/resendcreds/$",
        never_cache(ResendUserCredentials.as_view()),
        name="user-resendcredentials",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/delete/$",
        never_cache(UserDelete.as_view()),
        name="user-delete",
    ),
    re_path(
        r"^(?P<pk>[0-9]+)/assign_role/$",
        never_cache(UserAssignRole.as_view()),
        name="user-assign-role",
    ),
    re_path(
        r"^actions/",
        include(
            [
                re_path(
                    r"^mark-inactive$",
                    never_cache(MarkInactive.as_view()),
                    name="users-actions-markinactive",
                ),
            ]
        ),
    ),
    re_path(r"^(?P<pk>[0-9]+)/update/$", UserUpdate.as_view(), name="user-update"),
    re_path(r"^ac/all/$", AllPersons.as_view(), name="user-AllPersons-ac"),
    re_path(r"^ofs-autocomplete/$", OfsAutoComplete.as_view(), name="ofs-autocomplete"),
    re_path(r"^ac/coordinator/$", AllCoordinators.as_view(), name="user-coordinators"),
    re_path(
        r"^ac/prfs/$",
        PersonsRelevantForSessions.as_view(),
        name="user-PersonsRelevantForSessions-ac",
    ),
    re_path(r"^ac/helpers/$", Helpers.as_view(), name="user-Helpers-ac"),
    re_path(r"^ac/leaders/$", Leaders.as_view(), name="user-Leaders-ac"),
    re_path(r"^ac/actors/$", Actors.as_view(), name="user-Actors-ac"),
]
