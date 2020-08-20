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

from django import forms
from django.utils.translation import ugettext_lazy as _

from apps.user import FORMATION_M1, FORMATION_M2, formation_short

from . import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
)
from .models.availability import HelperSessionAvailability


class BSChoiceRadioSelect(forms.RadioSelect):
    template_name = "widgets/BSRadioSelect.html"
    option_template_name = "widgets/BSChoiceRadioSelect_option.html"

    def __init__(self, *args, **kwargs):
        # Trick to pass the 'at which role that user is
        # selected in that quali' information through
        self.user_assignment = kwargs.pop("user_assignment", False)
        return super(BSChoiceRadioSelect, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super(BSChoiceRadioSelect, self).get_context(name, value, attrs)
        # Avoid journal messages
        context["widget"]["forbid_absence"] = None
        # User has a status in the session, forbid change
        disable_all = self.user_assignment is not None
        for optgroup in context["widget"]["optgroups"]:
            (group, options, index) = optgroup
            # Avoid journal messages
            options[0]["glyphicon"] = None
            if options[0]["value"] == CHOSEN_AS_LEADER:
                options[0]["text"] = formation_short(FORMATION_M2)
                options[0]["class"] = "success"
            elif options[0]["value"] == CHOSEN_AS_HELPER:
                options[0]["text"] = formation_short(FORMATION_M1)
                options[0]["class"] = "success"
            elif options[0]["value"] == CHOSEN_AS_REPLACEMENT:
                options[0]["text"] = _("S")
                options[0]["class"] = "warning"
            elif options[0]["value"] == CHOSEN_AS_ACTOR:
                options[0]["glyphicon"] = "sunglasses"
                options[0]["class"] = "success"
            elif options[0]["value"] == CHOSEN_AS_LEGACY:
                options[0]["glyphicon"] = "ok-sign"
                options[0]["class"] = "warning"
            elif options[0]["value"] == CHOSEN_AS_NOT:
                options[0]["glyphicon"] = "remove-circle"
                options[0]["class"] = "default"
            options[0]["disabled"] = disable_all
        return context


class BSAvailabilityRadioSelect(forms.RadioSelect):
    template_name = "widgets/BSRadioSelect.html"
    option_template_name = "widgets/BSRadioSelect_option.html"

    def __init__(self, *args, **kwargs):
        self.forbid_absence = kwargs.pop("forbid_absence", False)
        return super(BSAvailabilityRadioSelect, self).__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super(BSAvailabilityRadioSelect, self).get_context(name, value, attrs)
        context["widget"]["forbid_absence"] = self.forbid_absence
        return context


class SessionChoiceField(object):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session", False)
        return super(SessionChoiceField, self).__init__(*args, **kwargs)

    def get_chosen_as(self, user):
        if not self.session:
            return
        try:
            return user.availabilities.get(session=self.session).chosen_as
        except HelperSessionAvailability.DoesNotExist:
            pass

    def if_replacement(self, user):
        return (
            " (%s)" % _("S")
            if self.get_chosen_as(user) == CHOSEN_AS_REPLACEMENT
            else ""
        )


class LeaderChoiceField(SessionChoiceField, forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s%s" % (obj.get_full_name(), self.if_replacement(obj))


class HelpersChoiceField(SessionChoiceField, forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "%s%s%s" % (
            obj.get_full_name(),
            (
                " (%s)" % obj.profile.formation
                if obj.profile.formation not in ["", FORMATION_M1]
                else ""
            ),
            self.if_replacement(obj),
        )


class ActorChoiceField(SessionChoiceField, forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{name} ({actor_for}){replacement}".format(
            name=obj.get_full_name(),
            actor_for=obj.profile.actor_inline,
            replacement=self.if_replacement(obj),
        )
