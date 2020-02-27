# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.utils.translation import ugettext_lazy as _

from multiselectfield.forms.fields import MultiSelectFormField

from apps.common import DV_STATE_CHOICES
from defivelo.roles import DV_AVAILABLE_ROLES

from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        allow_email = kwargs.pop("allow_email", False)
        # Whether to permit no-affiliation-canton creation
        affiliation_canton_required = kwargs.pop("affiliation_canton_required", True)
        cantons = kwargs.pop("cantons", None)
        super(UserProfileForm, self).__init__(*args, **kwargs)

        # Import all generated fields from UserProfile
        self.fields.update(modelform_factory(UserProfile, fields="__all__")().fields)
        del self.fields["user"]

        if not allow_email and "email" in self.fields:
            del self.fields["email"]
        for field in "first_name", "last_name", "email":
            if field in self.fields:
                self.fields[field].required = True

        if cantons:
            # Only permit edition within the allowed cantons
            choices = self.fields["affiliation_canton"].choices
            choices = (
                (k, v)
                for (k, v) in choices
                if k in cantons or (not affiliation_canton_required and k == "")
            )
            self.fields["affiliation_canton"].required = affiliation_canton_required
            self.fields["affiliation_canton"].choices = choices

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


class UserAssignRoleForm(forms.Form):
    role = forms.ChoiceField(
        label=_("Niveau d'accès"), choices=DV_AVAILABLE_ROLES, required=False
    )
    managed_states = MultiSelectFormField(
        label=_("Cantons gérés"), choices=sorted(DV_STATE_CHOICES), required=False
    )
