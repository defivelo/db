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

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import re_path
from django.utils.translation import gettext_lazy as _

from .views.common import HomeView, LicenseView

admin.autodiscover()

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    re_path(r"^accounts/", include("allauth.urls")),
    re_path(r"^license/", LicenseView.as_view(), name="license"),
    re_path(r"^agpl-", include("django_agpl.urls")),
    re_path(r"^article/", include("apps.article.urls")),
    re_path(r"^tinymce/", include("tinymce.urls")),
]

urlpatterns += i18n_patterns(
    re_path(r"^$", HomeView.as_view(), name="home"),
    re_path(r"^season/", include("apps.challenge.urls")),
    re_path(r"^orga/", include("apps.orga.urls")),
    re_path(r"^user/", include("apps.user.urls")),
    re_path(r"^info/", include("apps.info.urls")),
    re_path(r"^finance/", include("apps.salary.urls")),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        re_path(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

admin.site.site_header = _("Intranet DÉFI VÉLO")
