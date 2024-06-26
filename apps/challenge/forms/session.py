# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015-2020 Didier Raboud <didier.raboud@liip.ch>
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
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.defaultfilters import date
from django.utils.translation import gettext_lazy as _

from localflavor.ch.forms import CHStateSelect

from apps.common.forms import (
    CHPhoneNumberField,
    SwissDateField,
    SwissTimeField,
    UserAutoComplete,
)
from apps.user import STATE_CHOICES_WITH_DEFAULT
from apps.user.models import USERSTATUS_DELETED

from ..models import Session

nodate_change_warning = _(
    "La date ne peut plus être modifiée, car des heures ont déjà été "
    "saisies dans au moins une des Qualifs de cette session."
)


class SessionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop("cantons", None)
        self.season = kwargs.pop("season", None)
        is_for_coordinator = kwargs.pop("is_for_coordinator", False)

        super().__init__(**kwargs)
        if self.season.cantons:
            # Only permit orgas within the allowed cantons
            qs = self.fields["orga"].queryset.filter(
                address_canton__in=self.season.cantons
            )
            self.fields["orga"].queryset = qs

        # Disable minDate and maxDate - DEFIVELO-98
        # try:
        #     self.fields["day"].widget.options["minDate"] = self.season.begin.strftime(
        #         "%Y-%m-%d"
        #     )
        #     self.fields["day"].widget.options["maxDate"] = self.season.end.strftime(
        #         "%Y-%m-%d"
        #     )
        # except Exception:
        #     pass

        if is_for_coordinator:
            # For non-stateManagers (coordinator), set some fields disabled
            for f in ["orga", "day"]:
                self.fields[f].widget.attrs["readonly"] = True
                self.fields[f].disabled = True
            # And lots as hidden
            for f in list(self.fields.keys()):
                if f not in [
                    "orga",
                    "day",
                    "begin",
                    "fallback_plan",
                    "place",
                    "address_street",
                    "address_no",
                    "address_zip",
                    "address_city",
                    "address_canton",
                ]:
                    del self.fields[f]

        if self.instance.pk and self.instance.has_related_timesheets():
            self.fields["day"].help_text = nodate_change_warning
            self.fields["day"].widget.attrs["readonly"] = True

    day = SwissDateField(label=_("Date"))
    begin = SwissTimeField(label=_("Début"))
    address_canton = forms.ChoiceField(
        label=_("Canton"),
        widget=CHStateSelect,
        choices=STATE_CHOICES_WITH_DEFAULT,
        required=False,
    )
    apples = forms.CharField(
        label=_("Pommes"),
        required=False,
        widget=forms.TextInput(
            {
                "placeholder": _(
                    "Organisation de la livraison de pommes " "(quantité & logistique)"
                )
            }
        ),
    )
    helpers_time = SwissTimeField(
        label=_("Heure rendez-vous moniteurs"), required=False
    )
    superleader = UserAutoComplete(
        label=_("Moniteur + / Photographe"),
        queryset=(get_user_model().objects.exclude(profile__status=USERSTATUS_DELETED)),
        url="user-AllPersons-ac",
        required=False,
    )
    bikes_phone = CHPhoneNumberField(label=_("N° de contact vélos"), required=False)

    def clean_day(self):
        day = self.cleaned_data["day"]

        if self.instance.day != day and self.instance.has_related_timesheets():
            raise forms.ValidationError(nodate_change_warning)

        if self.season.begin <= day <= self.season.end:
            return day
        raise forms.ValidationError(
            _("La session doit être dans le mois" " (entre {begin} et {end})").format(
                begin=date(self.season.begin, settings.DATE_FORMAT),
                end=date(self.season.end, settings.DATE_FORMAT),
            )
        )

    class Meta:
        model = Session
        labels = {
            "orga": _("Établissement"),
        }
        fields = [
            "orga",
            "day",
            "begin",
            "fallback_plan",
            "place",
            "address_street",
            "address_no",
            "address_zip",
            "address_city",
            "address_canton",
            "superleader",
            "apples",
            "helpers_time",
            "helpers_place",
            "bikes_concept",
            "bikes_phone",
            "comments",
            "visible",
        ]


class SessionDeleteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.pop("cantons", None)
        self.season = kwargs.pop("season", None)
        super().__init__(**kwargs)

    class Meta:
        model = Session
        fields = []
