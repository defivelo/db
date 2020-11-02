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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from localflavor.ch.ch_states import STATE_CHOICES


class Address(models.Model):
    address_street = models.CharField(_("Rue"), max_length=255, blank=True)
    address_no = models.CharField(_("N°"), max_length=8, blank=True)
    address_additional = models.CharField(
        _("Complément d’adresse"), max_length=255, blank=True
    )
    address_zip = models.CharField(_("NPA"), max_length=4, blank=True)
    address_city = models.CharField(_("Ville"), max_length=64, blank=True)
    # Expand to 5 because of the special cantons
    address_canton = models.CharField(_("Canton"), max_length=2, blank=True)

    @property
    def address_canton_full(self):
        return [c[1] for c in STATE_CHOICES if c[0] == self.address_canton][0]
