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
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .views.common import HomeView, LicenseView

admin.autodiscover()

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^accounts/", include("allauth.urls")),
    url(r"^license/", LicenseView.as_view(), name="license"),
    url(r"^agpl-", include("django_agpl.urls")),
    url(r"^article/", include("apps.article.urls")),
    url(r"^tinymce/", include("tinymce.urls")),
]

urlpatterns += i18n_patterns(
    url(r"^$", HomeView.as_view(), name="home"),
    url(r"^season/", include("apps.challenge.urls")),
    url(r"^orga/", include("apps.orga.urls")),
    url(r"^user/", include("apps.user.urls")),
    url(r"^info/", include("apps.info.urls")),
    url(r"^finance/", include("apps.salary.urls")),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

admin.site.site_header = _("Intranet DÉFI VÉLO")
