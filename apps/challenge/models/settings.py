# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2020 Didier 'OdyX' Raboud <didier.raboud@liip.ch>
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


from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from simple_history.models import HistoricalRecords


class AnnualStateSetting(models.Model):
    canton = models.CharField(_("Canton"), max_length=2)
    year = models.PositiveSmallIntegerField(_("Année"))
    cost_per_bike = models.DecimalField(
        _("Coût par vélo"),
        decimal_places=2,
        max_digits=8,
        default=0,
        help_text=_("CHF"),
        validators=[MinValueValidator(0)],
    )
    cost_per_participant = models.DecimalField(
        _("Coût par participant"),
        decimal_places=2,
        max_digits=8,
        default=0,
        help_text=_("CHF"),
        validators=[MinValueValidator(0)],
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Configuration cantonale par année")
        verbose_name_plural = _("Configurations cantonales par année")
        unique_together = (("canton", "year"),)

    def __str__(self):
        return gettext(
            f"{self.year}: {self.canton} vélos: {self.cost_per_bike} participants: {self.cost_per_participant}"
        )
