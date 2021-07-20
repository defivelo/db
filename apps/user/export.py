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

from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from import_export import fields, resources, widgets

from defivelo.templatetags.dv_filters import canton_abbr, cantons_abbr

from .models import COLLABORATOR_FIELDS, STD_PROFILE_FIELDS


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
    ["first_name", "last_name", "email"]
    + [
        "profile__%s" % field
        for field in STD_PROFILE_FIELDS
        if field not in ["firstmed_course_comm"]
    ]
)
ALL_COLLABORATOR_FIELDS = tuple(
    ["first_name", "last_name", "email"]
    + ["profile__%s" % field for field in COLLABORATOR_FIELDS]
)


class UserResource(resources.ModelResource):
    first_name = fields.Field(column_name=_("Prénom"), attribute="first_name")
    last_name = fields.Field(column_name=_("Nom"), attribute="last_name")
    profile__language = fields.Field(
        column_name=_("Langue"), attribute="profile__language"
    )
    profile__languages_challenges = fields.Field(
        column_name=_("Prêt à animer en"),
        attribute="profile__languages_challenges",
        widget=MultipleSelectWidget(),
    )
    email = fields.Field(column_name=_("Email"), attribute="email")
    profile__natel = fields.Field(column_name=_("Natel"), attribute="profile__natel")
    profile__address_street = fields.Field(
        column_name=_("Rue"), attribute="profile__address_street"
    )
    profile__address_no = fields.Field(
        column_name=_("N°"), attribute="profile__address_no"
    )
    profile__address_zip = fields.Field(
        column_name=_("NPA"), attribute="profile__address_zip"
    )
    profile__address_city = fields.Field(
        column_name=_("Ville"), attribute="profile__address_city"
    )
    profile__address_canton = fields.Field(
        column_name=_("Canton de domicile"), attribute="profile__address_canton"
    )
    profile__birthdate = fields.Field(
        column_name=_("Date de naissance"),
        attribute="profile__birthdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    profile__nationality = fields.Field(
        column_name=_("Nationalité"), attribute="profile__nationality"
    )
    profile__work_permit = fields.Field(
        column_name=_("Permis de travail"), attribute="profile__work_permit"
    )
    profile__tax_jurisdiction = fields.Field(
        column_name=_("Lieu d’imposition"), attribute="profile__tax_jurisdiction"
    )
    profile__social_security = fields.Field(
        column_name=_("N° AVS"), attribute="profile__social_security"
    )
    profile__marital_status = fields.Field(
        column_name=_("État civil"),
        attribute="profile",
        widget=ObjectMethodWidget(method="marital_status_full"),
    )
    profile__pedagogical_experience = fields.Field(
        column_name=_("Expérience pédagogique"),
        attribute="profile__pedagogical_experience",
    )
    profile__comments = fields.Field(
        column_name=_("Commentaires"), attribute="profile__comments"
    )
    # From there, specific widgets
    profile__firstmed_course = fields.Field(
        column_name=_("Cours samaritains"), attribute="profile", widget=FirstMedWidget()
    )
    profile__actor_for = fields.Field(
        column_name=_("Intervenant"),
        attribute="profile",
        widget=ObjectMethodWidget(method="actor_inline"),
    )
    profile__status = fields.Field(
        column_name=_("Statut"),
        attribute="profile",
        widget=ObjectMethodWidget(method="status_full"),
    )
    profile__bagstatus = fields.Field(
        column_name=_("Sac Défi Vélo"),
        attribute="profile",
        widget=ObjectMethodWidget(method="bagstatus_full"),
    )
    profile__formation = fields.Field(
        column_name=_("Formation"),
        attribute="profile",
        widget=ObjectMethodWidget(method="formation_full"),
    )
    profile__formation_firstdate = fields.Field(
        column_name=_("Date de la première formation"),
        attribute="profile__formation_firstdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    profile__formation_lastdate = fields.Field(
        column_name=_("Date de la dernière formation"),
        attribute="profile__formation_lastdate",
        widget=widgets.DateWidget(format="%d.%m.%Y"),
    )
    profile__affiliation_canton = fields.Field(column_name=_("Canton d’affiliation"))
    profile__activity_cantons = fields.Field(
        column_name=_("Défi Vélo Mobile"),
        attribute="profile__activity_cantons",
        widget=MultipleSelectWidget(),
    )
    profile__employee_code = fields.Field(
        column_name=_("Numéro d’employé Crésus"),
        attribute="profile__employee_code",
    )
    profile__bank_name = fields.Field(
        column_name=_("Nom de la banque"),
        attribute="profile__bank_name",
    )
    profile__iban = fields.Field(
        column_name=_("IBAN"),
        attribute="profile__iban",
    )
    profile__access_level = fields.Field(
        column_name=_("Niveau d’accès"),
        attribute="profile",
        widget=ObjectMethodWidget(method="access_level_text"),
    )
    profile__managed_cantons = fields.Field(
        column_name=_("Cantons gérés"),
        attribute="profile",
        widget=ObjectMethodWidget(method="managed_cantons"),
    )

    class Meta:
        model = get_user_model()
        fields = ALL_PROFILE_FIELDS
        export_order = ALL_PROFILE_FIELDS

    def dehydrate_profile__address_canton(self, field):
        return canton_abbr(field.profile.address_canton, abbr=False, long=True)

    def dehydrate_profile__affiliation_canton(self, field):
        return canton_abbr(field.profile.affiliation_canton, abbr=False, long=True)

    def dehydrate_profile__activity_cantons(self, field):
        return ", ".join(
            cantons_abbr(field.profile.activity_cantons, abbr=False, long=True)
        )


class CollaboratorUserResource(UserResource):
    """
    Restricted UserResource
    """

    def get_fields(self, **kwargs):
        return [self.fields[f] for f in ALL_COLLABORATOR_FIELDS]
