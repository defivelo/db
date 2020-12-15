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

from django.core.exceptions import PermissionDenied
from django.utils.functional import cached_property

from defivelo.roles import user_cantons

from ..models import Season


class CantonSeasonFormMixin(object):
    allow_season_fetch = False

    @cached_property
    def season_object(self):
        """
        Return the season object without any constraints
        """
        try:
            seasonpk = int(
                self.kwargs["seasonpk"]
                if "seasonpk" in self.kwargs
                else self.kwargs["pk"]
            )
            return Season.objects.prefetch_related("leader").get(pk=seasonpk)
        except KeyError:
            return None

    @cached_property
    def season(self):
        """
        DEPRECATED
        This is too complicated, unreliable, so shouldn't be used anymore.
        self.season a Season object of the currently running season, with restrictions
        """
        try:
            season = self.season_object

            if not season:
                return None

            # Check that the intersection isn't empty
            usercantons = user_cantons(self.request.user)
            if usercantons and not list(
                set(usercantons).intersection(set(season.cantons))
            ):
                # If the user is marked as state manager for that season
                if season.leader == self.request.user:
                    return season
                # Verify that this state manager can access that canton as mobile
                if (
                    list(
                        set(
                            [self.request.user.profile.affiliation_canton]
                            + self.request.user.profile.activity_cantons
                        ).intersection(set(season.cantons))
                    )
                    and not self.raise_without_cantons
                ):
                    raise LookupError
                raise PermissionDenied
        except LookupError:
            # That user doesn't manage cantons
            if not self.allow_season_fetch:
                season = None
        except KeyError:
            # We're looking at a list
            season = None
        except Season.DoesNotExist:
            # I can't see it, or it doesn't exist
            raise ValueError("Can't see season or it doesn't exist")
        return season

    def get_form_kwargs(self):
        kwargs = super(CantonSeasonFormMixin, self).get_form_kwargs()
        kwargs["season"] = self.season_object
        try:
            cantons = user_cantons(self.request.user)
        except LookupError:
            cantons = None
        if self.season and cantons:
            # Check that one canton is in the intersection
            cantons = list(set(cantons).intersection(set(self.season.cantons)))
        kwargs["cantons"] = cantons
        return kwargs
