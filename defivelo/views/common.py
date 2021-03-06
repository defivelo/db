# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016 Didier Raboud <me+defivelo@odyx.org>
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
        context = super(MenuView, self).get_context_data(**kwargs)
        today = date.today()

        current_seasons = self.request.user.profile.get_seasons().filter(
            year=today.year
        )
        if date.today().month <= DV_SEASON_LAST_SPRING_MONTH:
            # Demi-année "printemps"
            current_seasons = current_seasons.filter(
                month_start__lte=DV_SEASON_LAST_SPRING_MONTH
            )
        else:
            # Demi-année "automne"
            current_seasons = current_seasons.filter(
                month_start__gt=DV_SEASON_LAST_SPRING_MONTH
            )

        context["current_seasons"] = current_seasons
        return context


class HomeView(MenuView, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        articles_qs = Article.objects
        if not has_permission(self.request.user, "home_article_crud"):
            articles_qs = articles_qs.filter(published=True)
        context["articles"] = articles_qs.order_by("-modified")[:5]
        # Add our menu_category context
        context["menu_category"] = "home"
        return context


class LicenseView(StrongholdPublicMixin, TemplateView):
    template_name = "license.html"
