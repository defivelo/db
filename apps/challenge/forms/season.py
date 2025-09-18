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
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker
from dal.forward import Const as dal_const
from dal_select2.widgets import ModelSelect2, Select2Multiple

from apps.common import (
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_RUNNING,
    DV_SEASON_STATES,
    DV_STATE_CHOICES_WITH_ABBR,
)
from apps.common.forms import SelectWithDisabledValues
from apps.user import FORMATION_KEYS, FORMATION_M2
from apps.user.models import USERSTATUS_DELETED

from ...orga.models import Organization
from .. import (
    AVAILABILITY_FIELDKEY,
    CHOICE_CHOICES,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
    SEASON_WORKWISH_FIELDKEY,
    STAFF_FIELDKEY,
)
from ..fields import BSAvailabilityRadioSelect, BSChoiceRadioSelect, LeaderChoiceField
from ..models import Season
from ..models.availability import HelperSessionAvailability


class SeasonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        cantons = kwargs.pop("cantons", None)
        kwargs.pop("season", None)
        super().__init__(**kwargs)
        self.fields["state"].widget = SelectWithDisabledValues(
            choices=self.fields["state"].choices,
            disabled_values=[DV_SEASON_STATE_RUNNING, DV_SEASON_STATE_OPEN],
        )

        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields["cantons"].choices
            choices = ((k, v) for (k, v) in choices if k in cantons)
            self.fields["cantons"].choices = choices

    year = forms.IntegerField(
        label=_("Année"),
        widget=DateTimePicker({"placeholder": "YYYY"}, options={"format": "YYYY"}),
    )
    leader = LeaderChoiceField(
        label=_("Chargé·e de projet"),
        queryset=(
            get_user_model()
            .objects.exclude(profile__status=USERSTATUS_DELETED)
            .filter(managedstates__isnull=False)
            .distinct()
        ),
        required=True,
    )

    class Meta:
        model = Season
        fields = ["year", "month_start", "n_months", "cantons", "state", "leader"]


class SeasonToSpecificStateForm(forms.ModelForm):
    """
    A form with hidden fields and a tickbox that will _only_ update a season to a specific season state
    """

    sendemail = forms.BooleanField(
        label=_("Envoyer le courriel suivant"), initial=True, required=False
    )
    customtext = forms.CharField(
        label=_("Précisions"),
        help_text=_(
            "Attention: Le courriel est envoyé à chaque destinataire dans sa langue, mais ce texte est envoyé tel quel, il ne sera pas traduit."
        ),
        initial="",
        widget=forms.Textarea,
        required=False,
    )

    def __init__(
        self,
        tostate: int,
        *args,
        **kwargs,
    ):
        """
        Takes a tostate argument, an int of desired target state
        """
        kwargs.pop("cantons", None)
        kwargs.pop("season", None)
        super().__init__(*args, **kwargs)
        # Only allow one target state
        state_choices = self.fields["state"].choices
        assert tostate in [k for (k, v) in DV_SEASON_STATES]
        self.fields["state"].choices = (
            (k, v) for (k, v) in state_choices if k == tostate
        )
        self.fields["state"].widget = forms.HiddenInput()

    class Meta:
        model = Season
        fields = ["state", "sendemail"]


class SeasonNewHelperAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        cantons = kwargs.pop("cantons", [])
        super(SeasonNewHelperAvailabilityForm, self).__init__(*args, **kwargs)
        self.fields["helper"] = forms.ModelChoiceField(
            label=_("Disponibilités pour :"),
            queryset=get_user_model()
            .objects.filter(
                Q(profile__formation__in=FORMATION_KEYS)
                | Q(profile__actor_for__isnull=False)
            )
            .exclude(profile__status=USERSTATUS_DELETED)
            .distinct(),
            widget=ModelSelect2(
                url="user-PersonsRelevantForSessions-ac",
                forward=[
                    dal_const(cantons, "cantons"),
                ],
            ),
        )


class SeasonAvailabilityForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop("instance")
        self.potential_helpers = kwargs.pop("potential_helpers")
        kwargs.pop("season", None)
        kwargs.pop("cantons", None)
        super(SeasonAvailabilityForm, self).__init__(*args, **kwargs)

        if self.potential_helpers:
            for helper_category, helpers in self.potential_helpers:
                for helper in helpers:
                    workwishkey = SEASON_WORKWISH_FIELDKEY.format(hpk=helper.pk)
                    try:
                        fieldinit = self.initial[workwishkey]
                    except KeyError:
                        fieldinit = 0
                    self.fields[workwishkey] = forms.IntegerField(
                        required=False,
                        initial=fieldinit,
                        min_value=0,
                    )

                    for session in self.season.sessions_with_qualifs:
                        availkey = AVAILABILITY_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk
                        )
                        staffkey = STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)
                        try:
                            fieldinit = self.initial[availkey]
                        except KeyError:
                            fieldinit = ""
                        try:
                            forbid_absence = self.initial[staffkey]
                        except KeyError:
                            forbid_absence = False
                        # Trick to pass the 'chosen' information through
                        self.fields[availkey] = forms.ChoiceField(
                            choices=HelperSessionAvailability.AVAILABILITY_CHOICES,
                            widget=BSAvailabilityRadioSelect(
                                forbid_absence=forbid_absence
                            ),
                            required=False,
                            initial=fieldinit,
                        )

    def save(self):
        pass


class SeasonStaffFilterForm(forms.Form):
    cantons = forms.MultipleChoiceField(
        label=_("Cantons"),
        choices=DV_STATE_CHOICES_WITH_ABBR,
        widget=Select2Multiple,
        required=False,
    )

    organisations = forms.MultipleChoiceField(
        label=_("Organisations"),
        choices=[],
        widget=Select2Multiple,
        required=False,
    )

    def __init__(self, organisations: list[Organization], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organisations:
            self.fields["organisations"].choices = [
                (orga.pk, str(orga))
                for orga in sorted(organisations, key=lambda o: str(o))
            ]
        else:
            del self.fields["organisations"]


class SeasonStaffChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.season = kwargs.pop("instance")
        self.available_helpers = kwargs.pop("available_helpers")
        kwargs.pop("season", None)
        kwargs.pop("cantons", None)
        super(SeasonStaffChoiceForm, self).__init__(*args, **kwargs)

        if self.available_helpers:
            for helper_category, helpers in self.available_helpers:
                for helper in helpers:
                    for session in self.season.sessions_with_qualifs:
                        AVAILABILITY_FIELDKEY.format(hpk=helper.pk, spk=session.pk)
                        staffkey = STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)
                        try:
                            fieldinit = self.initial[staffkey]
                        except KeyError:
                            fieldinit = CHOSEN_AS_NOT
                        available_choices = [CHOSEN_AS_NOT]
                        if helper.profile.actor:
                            available_choices.append(CHOSEN_AS_ACTOR)
                        if helper.profile.formation:
                            available_choices.append(CHOSEN_AS_HELPER)
                            available_choices.append(CHOSEN_AS_REPLACEMENT)
                        if helper.profile.formation == FORMATION_M2:
                            available_choices.append(CHOSEN_AS_LEADER)
                        self.fields[staffkey] = forms.ChoiceField(
                            choices=[
                                c
                                for c in list(CHOICE_CHOICES)
                                if c[0] in available_choices
                            ],
                            widget=BSChoiceRadioSelect(
                                attrs={"horizontal": True, "class": "btn-group-xs"},
                                user_assignment=session.user_assignment(helper),
                            ),
                            required=False,
                            initial=fieldinit,
                        )

    def save(self):
        pass
