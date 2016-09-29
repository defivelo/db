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
from django.views.decorators.cache import never_cache

from .views import (
    ResendUserCredentials, SendUserCredentials, UserCreate, UserDetail,
    UserList, UserListExport, UserUpdate,
)

urlpatterns = [
    url(r'^$', never_cache(UserList.as_view()), name="user-list"),
    url(r'^(?P<format>[a-z]+)export/$',
        never_cache(UserListExport.as_view()),
        name="user-list-export"),
    url(r'^new/$', UserCreate.as_view(), name="user-create"),
    url(r'^(?P<pk>[0-9]+)/$',
        never_cache(UserDetail.as_view()), name="user-detail"),
    url(r'^(?P<pk>[0-9]+)/sendcreds/$',
        never_cache(SendUserCredentials.as_view()),
        name="user-sendcredentials"),
    url(r'^(?P<pk>[0-9]+)/resendcreds/$',
        never_cache(ResendUserCredentials.as_view()),
        name="user-resendcredentials"),
    url(r'^me/$', never_cache(UserDetail.as_view()), name="profile-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', UserUpdate.as_view(), name="user-update"),
    url(r'^me/edit/$', UserUpdate.as_view(), name="profile-update"),
]
