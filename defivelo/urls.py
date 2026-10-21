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
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import include, re_path, reverse
from django.utils.translation import gettext_lazy as _

from .accounts import EmailView
from .views.common import HomeView, LicenseView

admin.autodiscover()


def _admin_login_redirect(request, extra_context=None):
    """
    Send anonymous visitors of /admin/login/ to the allauth login instead of
    Django admin's own (non-MFA-aware) login form. Already-authenticated
    visitors are routed to the admin index (if authorized) or home instead,
    since bouncing them back to the allauth login would redirect straight
    back here (via REDIRECT_FIELD_NAME) and loop forever.
    """
    if request.user.is_authenticated:
        if admin.site.has_permission(request):
            return redirect(reverse("admin:index"))
        return redirect(reverse("home"))
    return redirect_to_login(
        request.GET.get(REDIRECT_FIELD_NAME, reverse("admin:index")),
        login_url=reverse("account_login"),
    )


admin.site.login = _admin_login_redirect

urlpatterns = [
    re_path(r"^admin/", include("apps.email_outbox.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    re_path(r"^accounts/email/$", EmailView.as_view(), name="account_email"),
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
