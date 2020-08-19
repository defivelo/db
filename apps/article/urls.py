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

from .views import ArticleCreateView, ArticleDeleteView, ArticleUpdateView

urlpatterns = [
    url(r"^new/$", ArticleCreateView.as_view(), name="article-create"),
    url(
        r"^(?P<pk>[0-9]+)/update/$", ArticleUpdateView.as_view(), name="article-update"
    ),
    url(
        r"^(?P<pk>[0-9]+)/delete/$", ArticleDeleteView.as_view(), name="article-delete"
    ),
]
