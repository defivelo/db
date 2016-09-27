# -*- coding: utf-8 -*-
#
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

from article.models import Article
from django.utils import timezone
from django.views.generic.base import TemplateView

from apps.challenge.models import Season


class MenuView(object):
    def get_context_data(self, **kwargs):
        context = super(MenuView, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['current_seasons'] = \
            Season.objects.filter(end__gte=date.today())
        context['now'] = timezone.now()
        return context


class HomeView(MenuView, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['articles'] = Article.objects.order_by('-modified')[:5]
        # Add our menu_category context
        context['menu_category'] = 'home'
        return context


class LicenseView(MenuView, TemplateView):
    template_name = "license.html"
