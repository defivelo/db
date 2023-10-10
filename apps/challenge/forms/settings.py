# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2020 Didier Raboud <didier.raboud@liip.ch>
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

from django import forms
from django.utils.translation import gettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.ch.forms import CHStateSelect

from apps.common import DV_STATE_CHOICES

from ..models import AnnualStateSetting


class AnnualStateSettingForm(forms.ModelForm):
    year = forms.IntegerField(
        label=_("Année"),
        widget=DateTimePicker({"placeholder": "YYYY"}, options={"format": "YYYY"}),
        required=True,
    )
    canton = forms.ChoiceField(
        label=_("Canton"),
        widget=CHStateSelect,
        choices=DV_STATE_CHOICES,
        required=True,
    )

    class Meta:
        model = AnnualStateSetting
        fields = ["year", "canton", "cost_per_bike", "cost_per_participant"]

    def __init__(self, *args, **kwargs):
        year = kwargs.pop("year")
        cantons = kwargs.pop("cantons", None)
        super().__init__(*args, **kwargs)
        self.initial["year"] = year
        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields["canton"].choices
            choices = ((k, v) for (k, v) in choices if k in cantons)
            self.fields["canton"].choices = choices
