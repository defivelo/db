# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from import_export import fields, resources

from .models import Organization

ORGA_FIELDS = ['id', 'name', 'address_street', 'address_no',
               'address_additional', 'address_zip', 'address_city',
               'address_canton', 'created_on']


class OrganizationResource(resources.ModelResource):
    name = fields.Field(column_name=_('Nom'), attribute='name')
    address_street = fields.Field(column_name=_('Rue'),
                                  attribute='address_street')
    address_no = fields.Field(column_name=_('N°'),
                              attribute='address_no')
    address_additional = fields.Field(column_name=_("Complément d'adresse"),
                                      attribute='address_additional')
    address_zip = fields.Field(column_name=_('NPA'),
                               attribute='address_zip')
    address_city = fields.Field(column_name=_('Ville'),
                                attribute='address_city')
    address_canton = fields.Field(column_name=_('Canton'),
                                  attribute='address_canton')

    class Meta:
        model = Organization
        fields = ORGA_FIELDS
        export_order = ORGA_FIELDS