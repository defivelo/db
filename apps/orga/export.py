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

from django.utils.translation import gettext_lazy as _

from import_export import fields, resources

from defivelo.templatetags.dv_filters import canton_abbr

from . import ORGA_FIELDS
from .models import Organization

EXPORT_FIELDS = ["id", "created_on"] + ORGA_FIELDS


class OrganizationResource(resources.ModelResource):
    abbr = fields.Field(column_name=_("Abréviation"), attribute="abbr")
    name = fields.Field(column_name=_("Nom"), attribute="name")
    address_street = fields.Field(column_name=_("Rue"), attribute="address_street")
    address_no = fields.Field(column_name=_("N°"), attribute="address_no")
    address_additional = fields.Field(
        column_name=_("Complément d’adresse"), attribute="address_additional"
    )
    address_zip = fields.Field(column_name=_("NPA"), attribute="address_zip")
    address_city = fields.Field(column_name=_("Ville"), attribute="address_city")
    address_canton = fields.Field(
        column_name=_("Canton d’affiliation"), attribute="address_canton"
    )
    website = fields.Field(column_name=_("Site web"), attribute="website")
    coordinator_fullname = fields.Field(
        column_name=_("Coordina·teur·trice"), attribute="coordinator_fullname"
    )
    coordinator_phone = fields.Field(
        column_name=_("Téléphone"), attribute="coordinator_phone"
    )
    coordinator_natel = fields.Field(
        column_name=_("Natel"), attribute="coordinator_natel"
    )
    coordinator_email = fields.Field(
        column_name=_("Email"), attribute="coordinator_email"
    )
    status = fields.Field(column_name=_("Statut"), attribute="status_full")
    comments = fields.Field(column_name=_("Remarques"), attribute="comments")

    class Meta:
        model = Organization
        fields = EXPORT_FIELDS
        export_order = EXPORT_FIELDS

    def dehydrate_address_canton(self, field):
        return canton_abbr(field.address_canton, abbr=False, long=True)

    def dehydrate_coordinator_fullname(self, field):
        return field.coordinator.get_full_name() if field.coordinator else ""

    def dehydrate_coordinator_natel(self, field):
        return (
            field.coordinator.profile.natel
            if field.coordinator and field.coordinator.profile
            else ""
        )

    def dehydrate_coordinator_phone(self, field):
        return (
            field.coordinator.profile.phone
            if field.coordinator and field.coordinator.profile
            else ""
        )

    def dehydrate_coordinator_email(self, field):
        return field.coordinator.email if field.coordinator else ""
