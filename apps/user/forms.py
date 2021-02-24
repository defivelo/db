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

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import modelform_factory
from django.utils.translation import ugettext_lazy as _

from localflavor.ch.forms import (
    CHSocialSecurityNumberField,
    CHStateSelect,
    CHZipCodeField,
)
from localflavor.generic import forms as localforms
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from multiselectfield.forms.fields import MultiSelectFormField
from rolepermissions.roles import get_user_roles

from apps.common import DV_STATE_CHOICES
from apps.common.forms import (
    BS3CountriesField,
    CHPhoneNumberField,
    SelectWithDisabledValues,
    SwissDateField,
)
from apps.orga.models import Organization
from defivelo.roles import DV_AUTOMATIC_ROLES, DV_AVAILABLE_ROLES

from . import STATE_CHOICES_WITH_DEFAULT
from .models import UserProfile


class SimpleUserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        allow_email = kwargs.pop("allow_email", False)
        kwargs.pop("affiliation_canton_required", None)
        kwargs.pop("cantons", None)
        profile_fields = ["natel", "phone", "language", "comments"]
        if kwargs.pop("affiliation_canton", False):
            profile_fields.append("activity_cantons")
            profile_fields.append("affiliation_canton")
        super().__init__(*args, **kwargs)
        self.fields.update(
            modelform_factory(UserProfile, fields=profile_fields)().fields
        )

        # Some manual fixes lost by importing UserProfile
        for fieldname, fieldclass in {
            "natel": CHPhoneNumberField(required=False),
            "phone": CHPhoneNumberField(required=False),
        }.items():
            label = self.fields[fieldname].label
            self.fields[fieldname] = fieldclass
            self.fields[fieldname].label = label

        if not allow_email and "email" in self.fields:
            del self.fields["email"]

        for field in (
            "first_name",
            "last_name",
            "email",
            "language",
        ):
            if field in self.fields:
                self.fields[field].required = True

    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def clean_email(self):
        # Ideally, this should get checked by the User model
        email = self.cleaned_data["email"]
        existing_users = self._meta.model.objects.filter(email=email)
        if self.instance and self.instance.pk is not None:
            existing_users = existing_users.exclude(pk=self.instance.pk)
        if existing_users.exists():
            raise ValidationError(
                _("Un utilisateur avec cette adresse e-mail existe déjà.")
            )
        return email

    def clean(self):
        """
        Vérifie les contraintes croisées
        """
        cleaned_data = super().clean()

        try:
            affiliation_canton = cleaned_data["affiliation_canton"]
        except KeyError:
            affiliation_canton = None
        actor_for = (
            cleaned_data["actor_for"]
            if "actor_for" in cleaned_data
            else self.instance.profile.actor_for.all()
        )
        formation = (
            cleaned_data["formation"]
            if "formation" in cleaned_data
            else self.instance.profile.formation
        )
        if not affiliation_canton and (actor_for or formation):
            self.add_error(
                "affiliation_canton",
                ValidationError(
                    _("Moniteurs/intervenants ont besoin d’un canton d’affiliation.")
                ),
            )
        return cleaned_data


class UserProfileForm(SimpleUserProfileForm):
    def __init__(self, *args, **kwargs):
        # Whether to permit no-affiliation-canton creation
        affiliation_canton_required = kwargs.pop("affiliation_canton_required", True)
        cantons = kwargs.pop("cantons", None)
        super().__init__(*args, **kwargs)
        # Import all generated fields from UserProfile
        self.fields.update(modelform_factory(UserProfile, exclude=("user",))().fields)
        # Some manual fixes lost by importing UserProfile
        for fieldname, fieldclass in {
            "address_zip": CHZipCodeField(required=False),
            "birthdate": SwissDateField(required=False),
            "natel": CHPhoneNumberField(required=False),
            "phone": CHPhoneNumberField(required=False),
            "nationality": BS3CountriesField(required=False),
            "social_security": CHSocialSecurityNumberField(required=False),
            "address_canton": forms.ChoiceField(
                widget=CHStateSelect,
                choices=STATE_CHOICES_WITH_DEFAULT,
                required=False,
            ),
            "iban": localforms.IBANFormField(
                include_countries=IBAN_SEPA_COUNTRIES,
                required=False,
            ),
        }.items():
            label = self.fields[fieldname].label
            self.fields[fieldname] = fieldclass
            self.fields[fieldname].label = label
        # Some precisions
        self.fields["work_permit"].widget.attrs["placeholder"] = _("… si pas suisse")
        self.fields["tax_jurisdiction"].widget.attrs["placeholder"] = _(
            "… si pas en Suisse"
        )

        for field in (
            "first_name",
            "last_name",
            "email",
            "language",
            "affiliation_canton",
            "status",
        ):
            if field in self.fields:
                self.fields[field].required = True

        if cantons and "affiliation_canton" in self.fields:
            # if we edit a user from a other canton we cannot move him
            if (
                "affiliation_canton" in self.initial
                and self.initial["affiliation_canton"]
                and self.initial["affiliation_canton"] not in cantons
            ):
                self.fields["affiliation_canton"].disabled = True
            # Only permit edition within the allowed cantons
            choices = self.fields["affiliation_canton"].choices
            choices = (
                (k, v)
                for (k, v) in choices
                if k in cantons
                or k == ""
                or k == self.initial.get("affiliation_canton", "")
            )
            self.fields["affiliation_canton"].required = affiliation_canton_required
            self.fields["affiliation_canton"].choices = choices


class UserAssignRoleForm(forms.Form):
    role = forms.ChoiceField(
        label=_("Niveau d’accès"),
        choices=DV_AVAILABLE_ROLES,
        required=False,
        widget=SelectWithDisabledValues(
            choices=DV_AVAILABLE_ROLES,
            disabled_values=DV_AUTOMATIC_ROLES,
        ),
    )
    managed_states = MultiSelectFormField(
        label=_("Cantons gérés"), choices=sorted(DV_STATE_CHOICES), required=False
    )
    managed_organizations = MultiSelectFormField(
        label=_("Établissements gérés"),
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        roles = get_user_roles(user)
        self.fields["managed_organizations"].choices = [
            (orga.id, orga.name)
            for orga in Organization.objects.filter(
                Q(coordinator__isnull=True) | Q(coordinator=user)
            ).all()
        ]
        self.initial = {
            "role": roles[0].get_name() if len(roles) >= 1 else None,
            "managed_states": list(
                user.managedstates.all().values_list("canton", flat=True)
            ),
            "managed_organizations": list(
                user.managed_organizations.all().values_list("id", flat=True)
            ),
        }

    def save(self):
        role = self.cleaned_data["role"]
        self.user.profile.set_role(role)

        managed_states = self.cleaned_data["managed_states"]
        if role != "state_manager":
            managed_states = []
        self.user.profile.set_statemanager_for(managed_states)

        managed_organizations = self.cleaned_data["managed_organizations"]
        if role != "coordinator":
            managed_organizations = []
        self.user.managed_organizations.set(
            Organization.objects.filter(pk__in=managed_organizations)
        )
