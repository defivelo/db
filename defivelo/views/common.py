# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016, 2020 Didier Raboud <didier.raboud@liip.ch>
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

from datetime import date

from django.db.models import F
from django.views.generic.base import TemplateView

from stronghold.views import StrongholdPublicMixin

from apps.article.models import Article
from apps.common import DV_SEASON_AUTUMN, DV_SEASON_LAST_SPRING_MONTH, DV_SEASON_SPRING
from defivelo.roles import has_permission


class MenuView(object):
    def current_season(self):
        return (
            DV_SEASON_SPRING
            if date.today().month <= DV_SEASON_LAST_SPRING_MONTH
            else DV_SEASON_AUTUMN
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()

        # Uniquement les saisons==mois qui couvrent le jour courant
        context["current_seasons"] = self.request.user.profile.get_seasons().filter(
            year=today.year,
            month_start__lte=today.month,
            n_months__gt=today.month - F("month_start"),
        )
        return context


class HomeView(MenuView, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not has_permission(self.request.user, "coordinator_home"):
            articles_qs = Article.objects
            if not has_permission(self.request.user, "home_article_cud"):
                articles_qs = articles_qs.filter(published=True)
            context["articles"] = articles_qs.order_by("-modified")[:5]
        # Add our menu_category context
        context["menu_category"] = "home"
        return context

    def get_template_names(self):
        if has_permission(self.request.user, "coordinator_home"):
            self.template_name = "coordinator_home.html"
        else:
            self.template_name = "home.html"

        return super().get_template_names()


class LicenseView(StrongholdPublicMixin, TemplateView):
    template_name = "license.html"
