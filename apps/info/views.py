# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2017 Didier Raboud <me+defivelo@odyx.org>
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

from datetime import date
from django.views.generic.base import TemplateView
from stronghold.views import StrongholdPublicMixin

from apps.challenge.models.session import Session
from defivelo.views.common import MenuView


class PublicView(StrongholdPublicMixin):
    pass


class InfoCSS(PublicView, TemplateView):
    template_name = 'info/info.css'
    
    def render_to_response(self, context, **response_kwargs):
        return super(InfoCSS, self).render_to_response(
            context, content_type='text/css; charset=utf-8', **response_kwargs
        )
    
    def get_context_data(self, *args, **kwargs):
        context = super(InfoCSS, self).get_context_data(*args, **kwargs)
        context['colors'] = DV_STATE_COLORS
        return context


class NextQualifs(PublicView, TemplateView):
    template_name = 'info/next_qualifs.html'

    def get_context_data(self, *args, **kwargs):
        context = super(NextQualifs, self).get_context_data(*args, **kwargs)
        context['sessions'] = (
            Session.objects
            .filter(day__gte=date.today())
            .order_by('day', 'orga')
            .prefetch_related('orga')
        )
        return context
