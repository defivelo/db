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

from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources, widgets

from defivelo.templatetags.dv_filters import canton_abbr, cantons_abbr

from .models import STD_PROFILE_FIELDS, UserProfile


class MultipleSelectWidget(widgets.Widget):
    def render(self, value, obj=None):
        return ", ".join(value)


class FirstMedWidget(widgets.Widget):
    def render(self, value, object=None):
        final = _("Yes") if value.firstmed_course else _("No")
        if value.firstmed_course_comm:
            final += " - " + value.firstmed_course_comm
        return force_text(final)


class ObjectMethodWidget(widgets.Widget):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        return super(ObjectMethodWidget, self).__init__(*args, **kwargs)

    def render(self, value, object=None):
        attribute = getattr(value, self.method)
        if isinstance(attribute, list):
            attribute = ", ".join(attribute)
        if attribute:
            return force_text(attribute)
        return ""


ALL_PROFILE_FIELDS = tuple(
    ["user__%s" % f for f in ["first_name", "last_name", "email"]]
    + [f for f in STD_PROFILE_FIELDS if f not in ["firstmed_course_comm"]]
)


class UserResource(resources.ModelResource):
    user__first_name = fields.Field(
        column_name=_("Prénom"), attribute="user__first_name"
    )
    user__last_name = fields.Field(column_name=_("Nom"), attribute="user__last_name")
    user__email = fields.Field(column_name=_("Courriel"), attribute="user__email")
    language = fields.Field(column_name=_("Langue"), attribute="language")
    languages_challenges = fields.Field(
        column_name=_("Prêt à animer en"),
        attribute="languages_challenges",
        widget=MultipleSelectWidget(),
    )
    email = fields.Field(column_name=_("Email"), attribute="email")
    natel = fields.Field(column_name=_("Natel"), attribute="natel")
    address_street = fields.Field(column_name=_("Rue"), attribute="address_street")
    address_no = fields.Field(column_name=_("N°"), attribute="address_no")
    address_zip = fields.Field(column_name=_("NPA"), attribute="address_zip")
    address_city = fields.Field(column_name=_("Ville"), attribute="address_city")
    address_canton = fields.Field(
        column_name=_("Canton de domicile"), attribute="address_canton"
    )
    birthdate = fields.Field(
        column_name=_("Date de naissance"),
        attribute="birthdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    nationality = fields.Field(column_name=_("Nationalité"), attribute="nationality")
    work_permit = fields.Field(
        column_name=_("Permis de travail"), attribute="work_permit"
    )
    tax_jurisdiction = fields.Field(
        column_name=_("Lieu d'imposition"), attribute="tax_jurisdiction"
    )
    social_security = fields.Field(column_name=_("N° AVS"), attribute="social_security")
    marital_status = fields.Field(
        column_name=_("État civil"),
        attribute="profile",
        widget=ObjectMethodWidget(method="marital_status_full"),
    )
    pedagogical_experience = fields.Field(
        column_name=_("Expérience pédagogique"), attribute="pedagogical_experience",
    )
    comments = fields.Field(column_name=_("Commentaires"), attribute="comments")
    # From there, specific widgets
    firstmed_course = fields.Field(
        column_name=_("Cours samaritains"), attribute="profile", widget=FirstMedWidget()
    )
    actor_for = fields.Field(
        column_name=_("Intervenant"),
        attribute="profile",
        widget=ObjectMethodWidget(method="actor_inline"),
    )
    status = fields.Field(
        column_name=_("Statut"),
        attribute="profile",
        widget=ObjectMethodWidget(method="status_full"),
    )
    bagstatus = fields.Field(
        column_name=_("Sac Défi Vélo"),
        attribute="profile",
        widget=ObjectMethodWidget(method="bagstatus_full"),
    )
    formation = fields.Field(
        column_name=_("Formation"),
        attribute="profile",
        widget=ObjectMethodWidget(method="formation_full"),
    )
    formation_firstdate = fields.Field(
        column_name=_("Date de la première formation"),
        attribute="formation_firstdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    formation_lastdate = fields.Field(
        column_name=_("Date de la dernière formation"),
        attribute="formation_lastdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    affiliation_canton = fields.Field(column_name=_("Canton d'affiliation"))
    activity_cantons = fields.Field(
        column_name=_("Défi Vélo Mobile"),
        attribute="activity_cantons",
        widget=MultipleSelectWidget(),
    )
    cresus_employee_number = fields.Field(
        column_name=_("Numéro d'employé Crésus"), attribute="cresus_employee_number",
    )
    bank_name = fields.Field(column_name=_("Nom de la banque"), attribute="bank_name",)
    iban = fields.Field(
        column_name=_("IBAN"),
        attribute="profile",
        widget=ObjectMethodWidget(method="iban_nice"),
    )
    access_level = fields.Field(
        column_name=_("Niveau d'accès"),
        attribute="profile",
        widget=ObjectMethodWidget(method="access_level_text"),
    )
    managed_cantons = fields.Field(
        column_name=_("Cantons gérés"),
        attribute="profile",
        widget=ObjectMethodWidget(method="managed_cantons"),
    )

    class Meta:
        model = UserProfile
        fields = ALL_PROFILE_FIELDS
        export_order = ALL_PROFILE_FIELDS

    def dehydrate_address_canton(self, field):
        return canton_abbr(
            field.address_canton, abbr=False, long=True, fix_special=True
        )

    def dehydrate_affiliation_canton(self, field):
        return canton_abbr(
            field.affiliation_canton, abbr=False, long=True, fix_special=True
        )

    def dehydrate__activity_cantons(self, field):
        return ", ".join(
            cantons_abbr(
                field.activity_cantons, abbr=False, long=True, fix_special=True
            )
        )
