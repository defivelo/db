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
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from apps.common.forms import CHPhoneNumberField
from apps.user import FORMATION_KEYS, FORMATION_M2

from .. import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_REPLACEMENT,
    MAX_MONO1_PER_QUALI,
)
from ..fields import ActorChoiceField, HelpersChoiceField, LeaderChoiceField
from ..models import Qualification


class QualificationFormQuick(forms.ModelForm):
    class Meta:
        model = Qualification
        widgets = {
            "session": forms.HiddenInput,
            "name": forms.HiddenInput,
            "class_teacher_natel": forms.HiddenInput,
        }
        fields = ["session", "name", "class_teacher_natel"]


class QualificationForm(forms.ModelForm):
    class_teacher_natel = CHPhoneNumberField(
        label=_("Natel enseignant"), required=False
    )

    def __init__(self, *args, **kwargs):
        session = kwargs.pop("session")
        kwargs.pop("season", None)
        kwargs.pop("cantons", None)
        super(QualificationForm, self).__init__(*args, **kwargs)
        other_qualifs = session.qualifications.exclude(pk=self.instance.pk)
        # Construct chosen_as dict of arrays
        chosens = {}
        for avail in session.chosen_staff.all():
            if avail.chosen_as not in chosens:
                chosens[avail.chosen_as] = []
            chosens[avail.chosen_as].append(avail.helper_id)

        legacys = chosens.get(CHOSEN_AS_LEGACY, [])
        replacements = chosens.get(CHOSEN_AS_REPLACEMENT, [])
        leaders = legacys + replacements + chosens.get(CHOSEN_AS_LEADER, [])
        helpers = legacys + replacements + chosens.get(CHOSEN_AS_HELPER, [])
        actors = legacys + replacements + chosens.get(CHOSEN_AS_ACTOR, [])

        available_staff = get_user_model().objects.exclude(
            Q(qualifs_mon2__in=other_qualifs)
            | Q(qualifs_mon1__in=other_qualifs)
            | Q(qualifs_actor__in=other_qualifs)
        )
        self.fields["leader"] = LeaderChoiceField(
            label=_("Moniteur 2"),
            queryset=available_staff.filter(
                pk__in=leaders,
                profile__formation=FORMATION_M2,
            ),
            required=False,
            session=session,
        )
        self.fields["helpers"] = HelpersChoiceField(
            label=_("Moniteurs 1"),
            queryset=available_staff.filter(
                pk__in=helpers, profile__formation__in=FORMATION_KEYS
            ),
            required=False,
            session=session,
        )
        self.fields["actor"] = ActorChoiceField(
            label=_("Intervenant"),
            queryset=available_staff.filter(
                pk__in=actors, profile__actor_for__isnull=False
            ),
            required=False,
            session=session,
        )

    def clean_helpers(self):
        # Check that we don't have too many moniteurs 1
        helpers = self.cleaned_data.get("helpers")
        if helpers and helpers.count() > MAX_MONO1_PER_QUALI:
            raise ValidationError(
                _("Pas plus de %s moniteurs 1 !") % MAX_MONO1_PER_QUALI
            )
        # Check that all moniteurs are unique
        all_leaders_pk = []
        leader = self.cleaned_data.get("leader")
        if leader:
            all_leaders_pk.append(leader.pk)
        if helpers:
            for helper in helpers.all():
                all_leaders_pk.append(helper.pk)
        # Check unicity
        seen_pk = set()
        if len(
            [x for x in all_leaders_pk if x not in seen_pk and not seen_pk.add(x)]
        ) < len(all_leaders_pk):
            raise ValidationError(
                _("Il y a des moniteurs à double !"), code="double-helpers"
            )
        return helpers

    def clean_actor(self):
        # Check that the picked actor corresponds to the activity_C
        actor = self.cleaned_data.get("actor")
        activity_C = self.cleaned_data.get("activity_C")
        if actor:
            if activity_C:
                if not actor.profile.actor_for.filter(id=activity_C.id).exists():
                    raise ValidationError(
                        _(
                            "L’intervenant n’est pas qualifié pour la rencontre "
                            "prévue !"
                        ),
                        code="unqualified-actor",
                    )
            helpers = self.cleaned_data.get("helpers")
            if helpers and helpers.filter(id=actor.id).exists():
                raise ValidationError(
                    _("L’intervenant ne peut pas aussi être moniteur !"),
                    code="helper-actor",
                )
        return actor

    def clean(self):
        # Check that there are <= helmets or bikes than participants
        n_participants = self.cleaned_data.get("n_participants")
        if not n_participants:
            n_participants = 0
        n_bikes = self.cleaned_data.get("n_bikes")
        if n_bikes and int(n_bikes) > int(n_participants):
            raise ValidationError(
                _("Il y a trop de vélos prévus !"), code="too-many-bikes"
            )
        n_helmets = self.cleaned_data.get("n_helmets")
        if n_helmets and int(n_helmets) > int(n_participants):
            raise ValidationError(
                _("Il y a trop de casques prévus !"), code="too-many-helmets"
            )

        return self.cleaned_data

    class Meta:
        model = Qualification
        widgets = {"session": forms.HiddenInput}
        fields = [
            "session",
            "name",
            "class_teacher_fullname",
            "class_teacher_natel",
            "n_participants",
            "n_bikes",
            "n_helmets",
            "leader",
            "helpers",
            "activity_A",
            "activity_B",
            "activity_C",
            "actor",
            "comments",
        ]
