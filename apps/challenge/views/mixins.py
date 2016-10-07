# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

from django.core.exceptions import PermissionDenied

from defivelo.roles import user_cantons

from ..models import Season


class CantonSeasonFormMixin(object):
    @property
    def season(self):
        if not hasattr(self, '_season'):
            try:
                seasonpk = int(
                    self.kwargs['seasonpk'] if 'seasonpk' in self.kwargs
                    else self.kwargs['pk']
                )
                self._season = Season.objects.get(pk=seasonpk)

                # Check that the intersection isn't empty
                usercantons = user_cantons(self.request.user)
                if usercantons and not list(
                        set(usercantons)
                        .intersection(set(self._season.cantons))
                ):
                    raise PermissionDenied
            except KeyError:
                # We're looking at a list
                self._season = None
            except Season.DoesNotExist:
                # I can't see it, or it doesn't exist
                raise PermissionDenied
        return self._season

    def get_form_kwargs(self):
        kwargs = super(CantonSeasonFormMixin, self).get_form_kwargs()
        kwargs['season'] = self.season
        cantons = user_cantons(self.request.user)
        if self.season and cantons:
            # Check that one canton is in the intersection
            cantons = list(set(cantons).intersection(set(self.season.cantons)))
        kwargs['cantons'] = cantons
        return kwargs
